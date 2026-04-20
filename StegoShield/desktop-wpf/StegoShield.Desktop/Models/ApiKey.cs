using System;

namespace StegoShield.Desktop.Models
{
    public class ApiKey
    {
        public string Id { get; set; } = Guid.NewGuid().ToString();
        public string Name { get; set; } = string.Empty;
        public string Key { get; set; } = string.Empty;
        public string KeyPrefix { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.Now;
        public DateTime? LastUsedAt { get; set; }
        public bool IsActive { get; set; } = true;
        public int UsageCount { get; set; } = 0;
        public int RateLimitPerHour { get; set; } = 100;
    }
}
