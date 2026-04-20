using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

namespace StegoShield.Desktop.Services
{
    public class ActivationService
    {
        private static readonly Lazy<ActivationService> _instance = 
            new Lazy<ActivationService>(() => new ActivationService());
        
        public static ActivationService Instance => _instance.Value;

        private readonly HttpClient _httpClient;
        private const string ActivationServerUrl = "http://localhost:5001/api/v1/activation";
        private readonly string _activationCachePath;

        private ActivationService()
        {
            _httpClient = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(10)
            };

            var appDataPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "StegoShield"
            );
            Directory.CreateDirectory(appDataPath);
            _activationCachePath = Path.Combine(appDataPath, "activation.dat");
        }

        public async Task<(bool Success, string Message, int VipDays)> ValidateActivationCodeAsync(string code)
        {
            if (string.IsNullOrWhiteSpace(code))
            {
                return (false, "请输入激活码", 0);
            }

            code = code.Trim().ToUpper();

            // 优先使用本地离线验证（无需服务器）
            var offlineResult = ValidateOfflineCode(code);
            if (offlineResult.Success)
            {
                return offlineResult;
            }

            // 本地验证失败后，再尝试连接远程服务器
            try
            {
                var response = await _httpClient.PostAsync(
                    ActivationServerUrl,
                    new StringContent(
                        JsonSerializer.Serialize(new { code }),
                        System.Text.Encoding.UTF8,
                        "application/json"
                    )
                );

                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    var result = JsonSerializer.Deserialize<ActivationResponse>(json);

                    if (result?.Success == true)
                    {
                        return (true, result.Message ?? "激活成功！", result.Days);
                    }
                    else
                    {
                        return (false, result?.Message ?? "激活码无效", 0);
                    }
                }
                else
                {
                    return (false, "服务器错误，请稍后重试", 0);
                }
            }
            catch
            {
                // 如果本地验证失败且无法连接服务器，返回本地验证的错误消息
                return offlineResult;
            }
        }

        private (bool Success, string Message, int Days) ValidateOfflineCode(string code)
        {
            // 离线激活码验证（本地演示用）
            var validCodes = new Dictionary<string, int>
            {
                { "STEGO2024", 365 },      // 年度VIP
                { "STEGOMONTH", 30 },      // 月度VIP
                { "STEGOWEEK", 7 },         // 周VIP
                { "STEGO100", 100 },        // 100天VIP
                { "STEGO365", 365 },        // 365天VIP
                { "VIP2024", 365 },         // VIP年度
                { "TEST123", 30 },          // 测试码
                { "DEMO2024", 365 },        // 演示码
            };

            if (validCodes.TryGetValue(code, out int days))
            {
                return (true, $"激活成功！获得 {days} 天VIP会员", days);
            }

            return (false, "激活码无效，请检查后重试", 0);
        }

        public void SaveActivationCache(string code, int days, DateTime expiryDate)
        {
            try
            {
                var cache = new ActivationCache
                {
                    Code = code,
                    ActivatedAt = DateTime.Now,
                    ExpiryDate = expiryDate,
                    Days = days
                };

                var json = JsonSerializer.Serialize(cache);
                File.WriteAllText(_activationCachePath, json);
            }
            catch
            {
                // 忽略缓存保存失败
            }
        }

        public ActivationCache? LoadActivationCache()
        {
            try
            {
                if (File.Exists(_activationCachePath))
                {
                    var json = File.ReadAllText(_activationCachePath);
                    return JsonSerializer.Deserialize<ActivationCache>(json);
                }
            }
            catch
            {
                // 忽略缓存加载失败
            }

            return null;
        }

        public void ClearActivationCache()
        {
            try
            {
                if (File.Exists(_activationCachePath))
                {
                    File.Delete(_activationCachePath);
                }
            }
            catch
            {
                // 忽略缓存删除失败
            }
        }

        private class ActivationResponse
        {
            public bool Success { get; set; }
            public string? Message { get; set; }
            public int Days { get; set; }
        }
    }

    public class ActivationCache
    {
        public string Code { get; set; } = string.Empty;
        public DateTime ActivatedAt { get; set; }
        public DateTime ExpiryDate { get; set; }
        public int Days { get; set; }
    }
}
