using System;
using System.Diagnostics;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace StegoShield.Desktop.Services
{
    public class ApiService
    {
        private static readonly Lazy<ApiService> _instance = 
            new Lazy<ApiService>(() => new ApiService());
        
        public static ApiService Instance => _instance.Value;

        private readonly HttpClient _httpClient;
        private Process? _backendProcess;
        private const string BaseUrl = "http://127.0.0.1:5001/api";
        private bool _isBackendRunning = false;

        private ApiService()
        {
            _httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(5)
            };
        }

        private string FindBackendPath()
        {
            var possiblePaths = new[]
            {
                @"C:\Users\17544\.openclaw\workspace\main\StegoShield\desktop\backend"
            };

            foreach (var path in possiblePaths)
            {
                var runScript = Path.Combine(path, "run.py");
                if (File.Exists(runScript))
                {
                    return path;
                }
            }

            return string.Empty;
        }

        public void StartBackend()
        {
            if (_isBackendRunning) return;

            try
            {
                var backendPath = FindBackendPath();

                if (string.IsNullOrEmpty(backendPath))
                {
                    System.Windows.MessageBox.Show(
                        "未找到后端脚本！\n\n请手动启动Flask后端。", 
                        "错误", 
                        System.Windows.MessageBoxButton.OK, 
                        System.Windows.MessageBoxImage.Error
                    );
                    return;
                }

                var runScript = Path.Combine(backendPath, "run.py");

                var startInfo = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = "\"" + runScript + "\"",
                    WorkingDirectory = backendPath,
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                startInfo.Environment["FLASK_ENV"] = "development";
                startInfo.Environment["FLASK_DEBUG"] = "False";

                _backendProcess = new Process { StartInfo = startInfo };

                _backendProcess.OutputDataReceived += (s, e) =>
                {
                    if (e.Data != null && e.Data.Contains("Running on"))
                    {
                        _isBackendRunning = true;
                    }
                };

                _backendProcess.Start();
                _backendProcess.BeginOutputReadLine();

                Task.Run(async () =>
                {
                    int attempts = 0;
                    while (!_isBackendRunning && attempts < 30)
                    {
                        await Task.Delay(1000);
                        attempts++;
                        
                        try
                        {
                            var response = await _httpClient.GetAsync(BaseUrl + "/auth/login");
                            if (response.IsSuccessStatusCode)
                            {
                                _isBackendRunning = true;
                                break;
                            }
                        }
                        catch { }
                    }
                });
            }
            catch (Exception ex)
            {
                System.Windows.MessageBox.Show(
                    "启动后端失败: " + ex.Message, 
                    "错误", 
                    System.Windows.MessageBoxButton.OK, 
                    System.Windows.MessageBoxImage.Error
                );
            }
        }

        public void StopBackend()
        {
            if (_backendProcess != null && !_backendProcess.HasExited)
            {
                try
                {
                    _backendProcess.Kill();
                    _backendProcess.Dispose();
                }
                catch { }
                _backendProcess = null;
            }
            _isBackendRunning = false;
        }

        public async Task<LoginResponse> LoginAsync(string username, string password)
        {
            try
            {
                var data = new { username, password };
                var json = JsonConvert.SerializeObject(data);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync(BaseUrl + "/auth/login", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                return JsonConvert.DeserializeObject<LoginResponse>(responseJson) 
                    ?? new LoginResponse { Success = false, Message = "登录失败" };
            }
            catch (Exception ex)
            {
                return new LoginResponse 
                { 
                    Success = false, 
                    Message = "网络错误: " + ex.Message 
                };
            }
        }

        public async Task<LoginResponse> RegisterAsync(string username, string email, string password)
        {
            try
            {
                var data = new { username, email, password };
                var json = JsonConvert.SerializeObject(data);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await _httpClient.PostAsync(BaseUrl + "/auth/register", content);
                var responseJson = await response.Content.ReadAsStringAsync();
                
                return JsonConvert.DeserializeObject<LoginResponse>(responseJson) 
                    ?? new LoginResponse { Success = false, Message = "注册失败" };
            }
            catch (Exception ex)
            {
                return new LoginResponse 
                { 
                    Success = false, 
                    Message = "网络错误: " + ex.Message 
                };
            }
        }

        public async Task<bool> IsBackendRunningAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync("http://127.0.0.1:5001/");
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }
    }

    public class LoginResponse
    {
        public bool Success { get; set; }
        public string Message { get; set; }
        public UserData? Data { get; set; }
    }

    public class UserData
    {
        public int user_id { get; set; }
        public string username { get; set; }
        public string email { get; set; }
        public bool is_vip { get; set; }
        public int points { get; set; }
        public int use_count { get; set; }
        
        public string Initial
        {
            get
            {
                if (string.IsNullOrEmpty(username))
                    return "U";
                return username[0].ToString().ToUpper();
            }
        }
        
        public string StatusText
        {
            get
            {
                return is_vip ? "VIP用户" : "免费用户";
            }
        }
    }
}
