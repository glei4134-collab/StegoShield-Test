using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace StegoShield.Desktop.Services
{
    public class HttpServerService
    {
        private static readonly Lazy<HttpServerService> _instance = 
            new Lazy<HttpServerService>(() => new HttpServerService());
        
        public static HttpServerService Instance => _instance.Value;

        private HttpListener? _listener;
        private CancellationTokenSource? _cts;
        private Task? _serverTask;
        private bool _isRunning = false;
        private readonly ConcurrentDictionary<string, RateLimitInfo> _rateLimits = new ConcurrentDictionary<string, RateLimitInfo>();

        public event EventHandler<ServerStatusEventArgs>? StatusChanged;
        public event EventHandler<ApiRequestEventArgs>? RequestReceived;

        public bool IsRunning => _isRunning;
        public int Port { get; private set; } = 5001;

        private class RateLimitInfo
        {
            public int RequestCount { get; set; }
            public DateTime WindowStart { get; set; }
            public List<DateTime> Requests { get; set; } = new List<DateTime>();
        }

        public class ServerStatusEventArgs : EventArgs
        {
            public bool IsRunning { get; set; }
            public string Message { get; set; } = string.Empty;
            public int? Port { get; set; }
        }

        public class ApiRequestEventArgs : EventArgs
        {
            public string Method { get; set; } = string.Empty;
            public string Path { get; set; } = string.Empty;
            public DateTime Timestamp { get; set; }
        }

        public async Task<(bool Success, string Message)> StartServerAsync(int port = 5001)
        {
            if (_isRunning)
            {
                return (false, "服务器已经在运行中");
            }

            try
            {
                Port = port;
                _listener = new HttpListener();
                _listener.Prefixes.Add($"http://localhost:{port}/");
                _listener.Prefixes.Add($"http://127.0.0.1:{port}/");
                
                _cts = new CancellationTokenSource();
                
                _listener.Start();
                _isRunning = true;

                _ = Task.Run(() => ListenAsync(_cts.Token));

                StatusChanged?.Invoke(this, new ServerStatusEventArgs 
                { 
                    IsRunning = true, 
                    Message = $"API服务器已启动于 http://localhost:{port}",
                    Port = port
                });

                return (true, $"服务器已成功启动于端口 {port}");
            }
            catch (Exception ex)
            {
                _isRunning = false;
                var errorMessage = $"启动服务器失败: {ex.Message}";
                StatusChanged?.Invoke(this, new ServerStatusEventArgs 
                { 
                    IsRunning = false, 
                    Message = errorMessage 
                });
                return (false, errorMessage);
            }
        }

        public void StopServer()
        {
            if (!_isRunning) return;

            try
            {
                _cts?.Cancel();
                _listener?.Stop();
                _listener?.Close();
                _listener = null;
                _isRunning = false;
                _rateLimits.Clear();

                StatusChanged?.Invoke(this, new ServerStatusEventArgs 
                { 
                    IsRunning = false, 
                    Message = "API服务器已停止" 
                });
            }
            catch (Exception ex)
            {
                StatusChanged?.Invoke(this, new ServerStatusEventArgs 
                { 
                    IsRunning = false, 
                    Message = $"停止服务器时出错: {ex.Message}" 
                });
            }
        }

        private async Task ListenAsync(CancellationToken token)
        {
            while (!token.IsCancellationRequested && _listener != null && _listener.IsListening)
            {
                try
                {
                    var context = await _listener.GetContextAsync();
                    _ = Task.Run(() => HandleRequestAsync(context, token));
                }
                catch (ObjectDisposedException)
                {
                    break;
                }
                catch (HttpListenerException)
                {
                    break;
                }
                catch (Exception)
                {
                    // 继续监听
                }
            }
        }

        private async Task HandleRequestAsync(HttpListenerContext context, CancellationToken token)
        {
            var request = context.Request;
            var response = context.Response;

            RequestReceived?.Invoke(this, new ApiRequestEventArgs 
            { 
                Method = request.HttpMethod, 
                Path = request.RawUrl ?? "/",
                Timestamp = DateTime.Now
            });

            response.ContentType = "application/json";
            response.Headers.Add("Access-Control-Allow-Origin", "*");
            response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
            response.Headers.Add("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-Key");

            if (request.HttpMethod == "OPTIONS")
            {
                response.StatusCode = 200;
                response.Close();
                return;
            }

            string responseBody;
            int statusCode = 200;

            try
            {
                var apiKey = request.Headers["X-API-Key"];
                var isAuthenticated = !string.IsNullOrEmpty(apiKey) && 
                                     UserService.Instance.ValidateApiKey(apiKey);

                var path = request.RawUrl?.Split('?')[0] ?? "/";

                if (path.StartsWith("/api/v1/") && !isAuthenticated && path != "/api/v1/health")
                {
                    responseBody = JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "Unauthorized",
                        Message = "需要提供有效的API密钥"
                    });
                    statusCode = 401;
                }
                else if (path == "/api/v1/health" || path == "/health")
                {
                    responseBody = JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = true, 
                        Message = "OK",
                        Data = new { status = "running", port = Port, timestamp = DateTime.Now }
                    });
                }
                else if (path == "/api/v1/stego/encode" && request.HttpMethod == "POST")
                {
                    (responseBody, statusCode) = await HandleStegoEncodeAsync(request);
                }
                else if (path == "/api/v1/stego/decode" && request.HttpMethod == "POST")
                {
                    (responseBody, statusCode) = await HandleStegoDecodeAsync(request);
                }
                else if (path == "/api/v1/vip/status" && request.HttpMethod == "GET")
                {
                    (responseBody, statusCode) = await HandleVipStatusAsync(request, isAuthenticated ? apiKey : null);
                }
                else if (path == "/api/v1/keys" && request.HttpMethod == "GET")
                {
                    (responseBody, statusCode) = HandleGetApiKeys(request, isAuthenticated ? apiKey : null);
                }
                else if (path == "/api/v1/keys" && request.HttpMethod == "POST")
                {
                    (responseBody, statusCode) = await HandleCreateApiKeyAsync(request);
                }
                else if (path.StartsWith("/api/v1/keys/") && request.HttpMethod == "DELETE")
                {
                    var keyId = path.Split('/').Last();
                    (responseBody, statusCode) = HandleDeleteApiKey(keyId);
                }
                else
                {
                    responseBody = JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "NotFound",
                        Message = "未找到指定的API端点"
                    });
                    statusCode = 404;
                }
            }
            catch (Exception ex)
            {
                responseBody = JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "InternalServerError",
                    Message = ex.Message
                });
                statusCode = 500;
            }

            if (!CheckRateLimit(request, response, ref statusCode, out responseBody))
            {
                statusCode = 429;
            }

            response.StatusCode = statusCode;
            var buffer = Encoding.UTF8.GetBytes(responseBody);
            response.ContentLength64 = buffer.Length;
            await response.OutputStream.WriteAsync(buffer, 0, buffer.Length);
            response.Close();
        }

        private bool CheckRateLimit(HttpListenerRequest request, HttpListenerResponse response, 
                                    ref int statusCode, out string responseBody)
        {
            var apiKey = request.Headers["X-API-Key"] ?? request.RemoteEndPoint?.Address?.ToString() ?? "unknown";
            
            var now = DateTime.Now;
            var windowStart = now.AddHours(-1);

            if (_rateLimits.TryGetValue(apiKey, out var rateLimitInfo))
            {
                rateLimitInfo.Requests.RemoveAll(r => r < windowStart);
                
                if (rateLimitInfo.Requests.Count >= 100)
                {
                    responseBody = JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "RateLimitExceeded",
                        Message = "请求过于频繁，请稍后再试"
                    });
                    return false;
                }
                
                rateLimitInfo.Requests.Add(now);
            }
            else
            {
                _rateLimits[apiKey] = new RateLimitInfo 
                { 
                    Requests = new List<DateTime> { now } 
                };
            }

            response.Headers.Add("X-RateLimit-Limit", "100");
            response.Headers.Add("X-RateLimit-Remaining", 
                (100 - (_rateLimits[apiKey]?.Requests.Count ?? 0)).ToString());
            response.Headers.Add("X-RateLimit-Reset", 
                new DateTimeOffset(now.AddHours(1)).ToUnixTimeSeconds().ToString());

            responseBody = string.Empty;
            return true;
        }

        private async Task<(string Response, int StatusCode)> HandleStegoEncodeAsync(HttpListenerRequest request)
        {
            try
            {
                using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
                var body = await reader.ReadToEndAsync();
                var data = JsonConvert.DeserializeObject<StegoEncodeRequest>(body);

                if (data == null || string.IsNullOrEmpty(data.ImagePath) || string.IsNullOrEmpty(data.Text))
                {
                    return (JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "ValidationError",
                        Message = "缺少必需参数：ImagePath 和 Text"
                    }), 400);
                }

                var result = await StegoService.Instance.EncodeAsync(
                    data.ImagePath, 
                    data.Text, 
                    data.Algorithm ?? "LSB",
                    data.OutputPath
                );

                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = true, 
                    Message = "隐写成功",
                    Data = new 
                    {
                        output_path = result.OutputPath,
                        bytes_written = result.BytesWritten,
                        algorithm = result.Algorithm
                    }
                }), 200);
            }
            catch (Exception ex)
            {
                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "EncodeError",
                    Message = ex.Message
                }), 500);
            }
        }

        private async Task<(string Response, int StatusCode)> HandleStegoDecodeAsync(HttpListenerRequest request)
        {
            try
            {
                using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
                var body = await reader.ReadToEndAsync();
                var data = JsonConvert.DeserializeObject<StegoDecodeRequest>(body);

                if (data == null || string.IsNullOrEmpty(data.ImagePath))
                {
                    return (JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "ValidationError",
                        Message = "缺少必需参数：ImagePath"
                    }), 400);
                }

                var result = await StegoService.Instance.DecodeAsync(
                    data.ImagePath, 
                    data.Algorithm ?? "LSB"
                );

                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = true, 
                    Message = "提取成功",
                    Data = new 
                    {
                        extracted_text = result.ExtractedText,
                        confidence = result.Confidence,
                        algorithm = result.Algorithm
                    }
                }), 200);
            }
            catch (Exception ex)
            {
                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "DecodeError",
                    Message = ex.Message
                }), 500);
            }
        }

        private async Task<(string Response, int StatusCode)> HandleVipStatusAsync(HttpListenerRequest request, string? apiKey)
        {
            var user = UserService.Instance.GetCurrentUser();
            var isVip = user?.IsVip ?? false;

            return (JsonConvert.SerializeObject(new ApiResponse 
            { 
                Success = true, 
                Message = "获取VIP状态成功",
                Data = new 
                {
                    is_vip = isVip,
                    username = user?.Username ?? "anonymous",
                    expires_at = user?.VipExpiry?.ToString("yyyy-MM-dd HH:mm:ss") ?? "N/A"
                }
            }), 200);
        }

        private (string Response, int StatusCode) HandleGetApiKeys(HttpListenerRequest request, string? apiKey)
        {
            var user = UserService.Instance.GetCurrentUser();
            if (user == null)
            {
                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "Unauthorized",
                    Message = "用户未登录"
                }), 401);
            }

            var keys = UserService.Instance.GetApiKeys();
            return (JsonConvert.SerializeObject(new ApiResponse 
            { 
                Success = true, 
                Message = "获取API密钥列表成功",
                Data = keys.Select(k => new 
                {
                    id = k.Id,
                    name = k.Name,
                    key = k.Key.Substring(0, 8) + "..." + k.Key.Substring(k.Key.Length - 4),
                    created_at = k.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss"),
                    is_active = k.IsActive,
                    rate_limit_per_hour = k.RateLimitPerHour
                }).ToList()
            }), 200);
        }

        private async Task<(string Response, int StatusCode)> HandleCreateApiKeyAsync(HttpListenerRequest request)
        {
            try
            {
                using var reader = new StreamReader(request.InputStream, request.ContentEncoding);
                var body = await reader.ReadToEndAsync();
                var data = JsonConvert.DeserializeObject<CreateApiKeyRequest>(body);

                if (data == null || string.IsNullOrEmpty(data.Name))
                {
                    return (JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "ValidationError",
                        Message = "缺少必需参数：Name"
                    }), 400);
                }

                var user = UserService.Instance.GetCurrentUser();
                if (user == null)
                {
                    return (JsonConvert.SerializeObject(new ApiResponse 
                    { 
                        Success = false, 
                        Error = "Unauthorized",
                        Message = "用户未登录"
                    }), 401);
                }

                var apiKey = UserService.Instance.CreateApiKey(data.Name, data.RateLimitPerHour ?? 100);

                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = true, 
                    Message = "API密钥创建成功",
                    Data = new 
                    {
                        id = apiKey.Id,
                        name = apiKey.Name,
                        key = apiKey.Key,
                        created_at = apiKey.CreatedAt.ToString("yyyy-MM-dd HH:mm:ss"),
                        rate_limit_per_hour = apiKey.RateLimitPerHour,
                        warning = "请妥善保存此密钥，它只会显示一次"
                    }
                }), 201);
            }
            catch (Exception ex)
            {
                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "CreateKeyError",
                    Message = ex.Message
                }), 500);
            }
        }

        private (string Response, int StatusCode) HandleDeleteApiKey(string keyId)
        {
            var user = UserService.Instance.GetCurrentUser();
            if (user == null)
            {
                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "Unauthorized",
                    Message = "用户未登录"
                }), 401);
            }

            var success = UserService.Instance.DeleteApiKey(keyId);
            if (!success)
            {
                return (JsonConvert.SerializeObject(new ApiResponse 
                { 
                    Success = false, 
                    Error = "NotFound",
                    Message = "API密钥不存在"
                }), 404);
            }

            return (JsonConvert.SerializeObject(new ApiResponse 
            { 
                Success = true, 
                Message = "API密钥已删除"
            }), 200);
        }
    }

    public class ApiResponse
    {
        public bool Success { get; set; }
        public string? Error { get; set; }
        public string Message { get; set; } = string.Empty;
        public object? Data { get; set; }
    }

    public class StegoEncodeRequest
    {
        public string ImagePath { get; set; } = string.Empty;
        public string Text { get; set; } = string.Empty;
        public string? Algorithm { get; set; }
        public string? OutputPath { get; set; }
    }

    public class StegoDecodeRequest
    {
        public string ImagePath { get; set; } = string.Empty;
        public string? Algorithm { get; set; }
    }

    public class CreateApiKeyRequest
    {
        public string Name { get; set; } = string.Empty;
        public int? RateLimitPerHour { get; set; }
    }
}
