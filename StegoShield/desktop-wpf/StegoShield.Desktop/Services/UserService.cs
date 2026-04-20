using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Newtonsoft.Json;
using StegoShield.Desktop.Models;

namespace StegoShield.Desktop.Services
{
    public class UserService
    {
        private static readonly Lazy<UserService> _instance = 
            new Lazy<UserService>(() => new UserService());
        
        public static UserService Instance => _instance.Value;

        private readonly string _usersFilePath;
        private readonly CryptoService _crypto;
        private UserData _userData;
        private User? _currentUser;

        private UserService()
        {
            System.Diagnostics.Debug.WriteLine("UserService正在初始化...");
            try
            {
                _crypto = CryptoService.Instance;
                System.Diagnostics.Debug.WriteLine("CryptoService获取成功");
                
                var appDataPath = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "StegoShield"
                );
                Directory.CreateDirectory(appDataPath);
                _usersFilePath = Path.Combine(appDataPath, "users.dat");
                System.Diagnostics.Debug.WriteLine($"用户文件路径: {_usersFilePath}");

                _userData = LoadUserData();
                System.Diagnostics.Debug.WriteLine($"用户数据加载成功，共{_userData?.Users?.Count ?? 0}个用户");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"UserService初始化失败: {ex}");
                throw;
            }
        }

        private UserData LoadUserData()
        {
            try
            {
                if (File.Exists(_usersFilePath))
                {
                    var encryptedData = File.ReadAllText(_usersFilePath);
                    var decryptedData = _crypto.Decrypt(encryptedData);
                    return JsonConvert.DeserializeObject<UserData>(decryptedData) ?? new UserData();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载用户数据失败: {ex.Message}");
            }
            
            return new UserData();
        }

        private void SaveUserData()
        {
            try
            {
                var json = JsonConvert.SerializeObject(_userData, Formatting.Indented);
                var encryptedData = _crypto.Encrypt(json);
                File.WriteAllText(_usersFilePath, encryptedData);
            }
            catch (Exception ex)
            {
                throw new Exception($"保存用户数据失败: {ex.Message}", ex);
            }
        }

        public User? CurrentUser => _currentUser;

        public bool IsLoggedIn => _currentUser != null;

        public async Task<(bool Success, string Message)> RegisterAsync(string username, string email, string password)
        {
            return await Task.Run(() =>
            {
                if (string.IsNullOrWhiteSpace(username))
                    return (false, "用户名不能为空");

                if (string.IsNullOrWhiteSpace(email))
                    return (false, "邮箱不能为空");

                if (string.IsNullOrWhiteSpace(password))
                    return (false, "密码不能为空");

                // 密码强度检查
                if (password.Length < 6)
                    return (false, "密码长度至少6位");
                
                if (password.Length < 8)
                    return (false, "密码建议至少8位以提高安全性");
                
                // 检查密码复杂度
                var hasUpper = password.Any(char.IsUpper);
                var hasLower = password.Any(char.IsLower);
                var hasDigit = password.Any(char.IsDigit);
                
                if (!hasUpper || !hasLower || !hasDigit)
                    return (false, "密码必须包含大小写字母和数字");

                if (_userData.Users.Any(u => u.Username.Equals(username, StringComparison.OrdinalIgnoreCase)))
                    return (false, "用户名已存在");

                if (_userData.Users.Any(u => u.Email.Equals(email, StringComparison.OrdinalIgnoreCase)))
                    return (false, "邮箱已被注册");

                var user = new User
                {
                    Id = Guid.NewGuid().ToString(),
                    Username = username.Trim(),
                    Email = email.Trim().ToLower(),
                    PasswordHash = _crypto.HashPassword(password),
                    CreatedAt = DateTime.Now,
                    IsVip = false,
                    Settings = new UserSettings()
                };

                _userData.Users.Add(user);
                SaveUserData();

                return (true, "注册成功！");
            });
        }

        public async Task<(bool Success, string Message)> LoginAsync(string username, string password)
        {
            return await Task.Run(() =>
            {
                try
                {
                    if (string.IsNullOrWhiteSpace(username))
                        return (false, "用户名不能为空");

                    if (string.IsNullOrWhiteSpace(password))
                        return (false, "密码不能为空");

                    var user = _userData.Users.FirstOrDefault(u => 
                        u.Username.Equals(username, StringComparison.OrdinalIgnoreCase));

                    if (user == null)
                        return (false, "用户不存在");

                    // 检查账户是否被锁定
                    if (user.LockedUntil.HasValue && user.LockedUntil.Value > DateTime.Now)
                    {
                        var remainingMinutes = (int)(user.LockedUntil.Value - DateTime.Now).TotalMinutes;
                        var loginRecord = new LoginRecord
                        {
                            Timestamp = DateTime.Now,
                            IpAddress = "127.0.0.1",
                            Success = false,
                            FailureReason = $"账户被锁定，剩余{remainingMinutes}分钟"
                        };
                        user.LoginHistory.Add(loginRecord);
                        SaveUserData();
                        return (false, $"账户已被锁定，请在{remainingMinutes}分钟后重试");
                    }

                    // 检查密码强度（首次登录或未设置强密码）
                    if (string.IsNullOrEmpty(user.PasswordHash))
                        return (false, "用户密码未设置");

                    if (!_crypto.VerifyPassword(password, user.PasswordHash))
                    {
                        // 登录失败处理
                        user.LoginFailedCount++;
                        
                        // 连续失败5次后锁定账户15分钟
                        if (user.LoginFailedCount >= 5)
                        {
                            user.LockedUntil = DateTime.Now.AddMinutes(15);
                            var loginRecord = new LoginRecord
                            {
                                Timestamp = DateTime.Now,
                                IpAddress = "127.0.0.1",
                                Success = false,
                                FailureReason = $"密码错误，连续失败{user.LoginFailedCount}次，账户被锁定15分钟"
                            };
                            user.LoginHistory.Add(loginRecord);
                            SaveUserData();
                            return (false, $"密码错误次数过多，账户已被锁定15分钟");
                        }
                        
                        var record = new LoginRecord
                        {
                            Timestamp = DateTime.Now,
                            IpAddress = "127.0.0.1",
                            Success = false,
                            FailureReason = $"密码错误（第{user.LoginFailedCount}次）"
                        };
                        user.LoginHistory.Add(record);
                        SaveUserData();
                        return (false, $"密码错误（剩余{5 - user.LoginFailedCount}次）");
                    }

                    // 登录成功
                    user.LoginFailedCount = 0;  // 重置失败计数
                    user.LockedUntil = null;  // 解除锁定
                    user.LastLoginAt = DateTime.Now;
                    
                    var successRecord = new LoginRecord
                    {
                        Timestamp = DateTime.Now,
                        IpAddress = "127.0.0.1",
                        Success = true,
                        FailureReason = ""
                    };
                    user.LoginHistory.Add(successRecord);
                    
                    // 只保留最近100条登录记录
                    if (user.LoginHistory.Count > 100)
                    {
                        user.LoginHistory = user.LoginHistory
                            .OrderByDescending(r => r.Timestamp)
                            .Take(100)
                            .ToList();
                    }
                    
                    SaveUserData();

                    _currentUser = user;
                    return (true, "登录成功！");
                }
                catch (Exception ex)
                {
                    System.Diagnostics.Debug.WriteLine($"登录异常: {ex}");
                    return (false, $"系统错误: {ex.GetType().Name}");
                }
            });
        }

        public void Logout()
        {
            _currentUser = null;
        }

        public async Task<(bool Success, string Message)> UpdatePasswordAsync(string oldPassword, string newPassword)
        {
            return await Task.Run(() =>
            {
                if (_currentUser == null)
                    return (false, "未登录");

                if (string.IsNullOrWhiteSpace(newPassword))
                    return (false, "新密码不能为空");

                if (newPassword.Length < 6)
                    return (false, "密码长度至少6位");

                if (!_crypto.VerifyPassword(oldPassword, _currentUser.PasswordHash))
                    return (false, "原密码错误");

                _currentUser.PasswordHash = _crypto.HashPassword(newPassword);
                SaveUserData();

                return (true, "密码修改成功！");
            });
        }

        public async Task<(bool Success, string Message)> UpdateEmailAsync(string email)
        {
            return await Task.Run(() =>
            {
                if (_currentUser == null)
                    return (false, "未登录");

                if (string.IsNullOrWhiteSpace(email))
                    return (false, "邮箱不能为空");

                if (_userData.Users.Any(u => u.Email.Equals(email, StringComparison.OrdinalIgnoreCase) && u.Id != _currentUser.Id))
                    return (false, "邮箱已被其他用户使用");

                _currentUser.Email = email.Trim().ToLower();
                SaveUserData();

                return (true, "邮箱修改成功！");
            });
        }

        public async Task<(bool Success, string Message)> UpdateSettingsAsync(UserSettings settings)
        {
            return await Task.Run(() =>
            {
                if (_currentUser == null)
                    return (false, "未登录");

                _currentUser.Settings = settings;
                SaveUserData();

                return (true, "设置已保存！");
            });
        }

        public bool IsVip()
        {
            if (_currentUser == null)
                return false;

            if (!_currentUser.IsVip)
                return false;

            if (_currentUser.VipExpiry.HasValue && _currentUser.VipExpiry.Value < DateTime.Now)
            {
                _currentUser.IsVip = false;
                _currentUser.VipExpiry = null;
                SaveUserData();
                return false;
            }

            return true;
        }

        public async Task<(bool Success, string Message)> ActivateVipAsync(DateTime expiryDate)
        {
            return await Task.Run(() =>
            {
                if (_currentUser == null)
                    return (false, "未登录");

                _currentUser.IsVip = true;
                _currentUser.VipExpiry = expiryDate;
                SaveUserData();

                return (true, $"VIP激活成功！到期时间: {expiryDate:yyyy-MM-dd}");
            });
        }

        public User? GetCurrentUser()
        {
            return _currentUser;
        }

        public ApiKey CreateApiKey(string name, int rateLimitPerHour = 100)
        {
            if (_currentUser == null)
                throw new InvalidOperationException("用户未登录");

            var apiKey = new ApiKey
            {
                Id = Guid.NewGuid().ToString(),
                Name = name,
                Key = _crypto.GenerateApiKey(),
                CreatedAt = DateTime.Now,
                IsActive = true,
                RateLimitPerHour = rateLimitPerHour
            };

            _currentUser.ApiKeys.Add(apiKey);
            SaveUserData();

            return apiKey;
        }

        public List<ApiKey> GetApiKeys()
        {
            if (_currentUser == null)
                return new List<ApiKey>();

            return _currentUser.ApiKeys.ToList();
        }

        public bool DeleteApiKey(string keyId)
        {
            if (_currentUser == null)
                return false;

            var key = _currentUser.ApiKeys.FirstOrDefault(k => k.Id == keyId);
            if (key == null)
                return false;

            _currentUser.ApiKeys.Remove(key);
            SaveUserData();
            return true;
        }

        public bool ValidateApiKey(string apiKey)
        {
            if (string.IsNullOrEmpty(apiKey))
                return false;

            return _userData.Users
                .SelectMany(u => u.ApiKeys)
                .Any(k => k.Key == apiKey && k.IsActive);
        }

        public static async Task<(bool Success, string Message)> RegisterAdminAsync(string username, string email, string password)
        {
            var instance = Instance;
            return await instance.RegisterAsync(username, email, password);
        }

        public static async Task<(bool Success, string Message)> ActivateAdminVipAsync(int years = 100)
        {
            var instance = Instance;
            if (instance._currentUser == null)
                return (false, "未登录");

            var expiryDate = DateTime.Now.AddYears(years);
            return await instance.ActivateVipAsync(expiryDate);
        }

        private class UserData
        {
            public string Version { get; set; } = "1.0";
            public DateTime CreatedAt { get; set; } = DateTime.Now;
            public List<User> Users { get; set; } = new List<User>();
        }
    }
}
