using System;
using System.Collections.Generic;

namespace StegoShield.Desktop.Models
{
    public class User
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Username { get; set; } = string.Empty;
        public string Email { get; set; } = string.Empty;
        public string PasswordHash { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
        public DateTime? LastLoginAt { get; set; }
        public bool IsVip { get; set; } = false;
        public DateTime? VipExpiry { get; set; }
        
        // 账户安全相关
        public int LoginFailedCount { get; set; } = 0;  // 连续登录失败次数
        public DateTime? LockedUntil { get; set; }  // 账户锁定截止时间
        public List<LoginRecord> LoginHistory { get; set; } = new List<LoginRecord>();  // 登录历史
        
        public UserSettings Settings { get; set; } = new UserSettings();
        public List<ApiKey> ApiKeys { get; set; } = new List<ApiKey>();
    }
    
    public class LoginRecord
    {
        public DateTime Timestamp { get; set; } = DateTime.Now;
        public string IpAddress { get; set; } = string.Empty;
        public bool Success { get; set; }
        public string FailureReason { get; set; } = string.Empty;
    }

    public class UserSettings
    {
        public bool RememberMe { get; set; } = false;
        public string DefaultOutputPath { get; set; } = string.Empty;
        public int ImageQuality { get; set; } = 95;
        public bool KeepBackup { get; set; } = true;
        public string Theme { get; set; } = "Light";
        public int AutoLockMinutes { get; set; } = 0;
        public bool EnableNotifications { get; set; } = true;
        public bool EnableSound { get; set; } = true;
    }
}
