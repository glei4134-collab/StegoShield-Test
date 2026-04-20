using System;

namespace StegoShield.Desktop.Models
{
    public class StegoResult
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string? OutputPath { get; set; }
        public byte[]? OutputData { get; set; }
        public string? ExtractedText { get; set; }
        public string? Metadata { get; set; }
        public string Algorithm { get; set; } = string.Empty;
        public double ProcessingTime { get; set; }
        public long OriginalSize { get; set; }
        public long OutputSize { get; set; }
        public long BytesWritten { get; set; }
        public double Confidence { get; set; }
        public double CompressionRatio { get; set; }
    }

    public class StegoImage
    {
        public string FilePath { get; set; } = string.Empty;
        public byte[] ImageData { get; set; } = Array.Empty<byte>();
        public int Width { get; set; }
        public int Height { get; set; }
        public string Format { get; set; } = string.Empty;
        public long FileSize { get; set; }

        public static StegoImage LoadFromFile(string filePath)
        {
            var fileInfo = new System.IO.FileInfo(filePath);
            var imageData = System.IO.File.ReadAllBytes(filePath);
            
            using (var ms = new System.IO.MemoryStream(imageData))
            using (var img = System.Drawing.Image.FromStream(ms))
            {
                return new StegoImage
                {
                    FilePath = filePath,
                    ImageData = imageData,
                    Width = img.Width,
                    Height = img.Height,
                    Format = img.RawFormat.ToString(),
                    FileSize = fileInfo.Length
                };
            }
        }
    }

    public class StegoAlgorithm
    {
        public string Name { get; set; } = string.Empty;
        public string DisplayName { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public bool IsVipOnly { get; set; }
        public bool SupportsBatch { get; set; }
        public int MaxDataSize { get; set; }
        public string[] SupportedFormats { get; set; } = Array.Empty<string>();
    }
}
