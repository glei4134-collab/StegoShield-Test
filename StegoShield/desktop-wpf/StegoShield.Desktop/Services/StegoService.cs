using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using StegoShield.Desktop.Models;

namespace StegoShield.Desktop.Services
{
    public class StegoService
    {
        private static readonly Lazy<StegoService> _instance = 
            new Lazy<StegoService>(() => new StegoService());
        
        public static StegoService Instance => _instance.Value;

        private StegoService()
        {
            InitializeAlgorithms();
        }

        private void InitializeAlgorithms()
        {
            AvailableAlgorithms = new List<StegoAlgorithm>
            {
                new StegoAlgorithm
                {
                    Name = "lsb",
                    DisplayName = "LSB (PNG 推荐)",
                    Description = "最基础的隐写算法，将数据嵌入到图片像素的最低位",
                    IsVipOnly = false,
                    SupportsBatch = false,
                    MaxDataSize = 1024 * 1024, // 1MB
                    SupportedFormats = new[] { "PNG", "BMP", "TIFF" }
                },
                new StegoAlgorithm
                {
                    Name = "dct",
                    DisplayName = "DCT (JPEG 支持)",
                    Description = "适合JPEG格式的高级隐写算法",
                    IsVipOnly = true,
                    SupportsBatch = true,
                    MaxDataSize = 5 * 1024 * 1024, // 5MB
                    SupportedFormats = new[] { "JPEG", "PNG" }
                }
            };
        }

        public List<StegoAlgorithm> AvailableAlgorithms { get; private set; } = new List<StegoAlgorithm>();

        public async Task<StegoResult> EncodeAsync(string imagePath, string textData, string algorithm = "lsb", string? outputPath = null, bool useEncryption = false, bool useRedundancy = false, string? encryptionKey = null)
        {
            return await Task.Run(() =>
            {
                var sw = Stopwatch.StartNew();
                
                try
                {
                    if (!File.Exists(imagePath))
                        return new StegoResult 
                        { 
                            Success = false, 
                            Message = "图片文件不存在" 
                        };

                    if (string.IsNullOrEmpty(textData))
                        return new StegoResult 
                        { 
                            Success = false, 
                            Message = "要嵌入的数据不能为空" 
                        };

                    byte[] dataBytes = Encoding.UTF8.GetBytes(textData);

                    if (useEncryption && !string.IsNullOrEmpty(encryptionKey))
                    {
                        var (encrypted, _) = CryptoService.Instance.EncryptBytes(dataBytes, encryptionKey);
                        dataBytes = encrypted;
                    }

                    if (useRedundancy)
                    {
                        dataBytes = CryptoService.Instance.EncodeWithRedundancy(dataBytes);
                    }

                    var image = StegoImage.LoadFromFile(imagePath);
                    
                    if (outputPath == null)
                    {
                        var directory = Path.GetDirectoryName(imagePath);
                        var fileName = Path.GetFileNameWithoutExtension(imagePath);
                        var extension = Path.GetExtension(imagePath);
                        outputPath = Path.Combine(directory ?? "", $"{fileName}_stego{extension}");
                    }

                    StegoResult result;

                    switch (algorithm.ToLower())
                    {
                        case "lsb":
                            result = EncodeLSB(image, dataBytes);
                            break;
                        case "dct":
                            result = new StegoResult 
                            { 
                                Success = false, 
                                Message = "DCT算法需要VIP会员" 
                            };
                            break;
                        default:
                            result = EncodeLSB(image, dataBytes);
                            break;
                    }

                    if (result.Success && result.OutputData != null)
                    {
                        File.WriteAllBytes(outputPath, result.OutputData);
                        result.OutputPath = outputPath;
                    }

                    sw.Stop();
                    result.ProcessingTime = sw.Elapsed.TotalSeconds;
                    result.Algorithm = algorithm;

                    return result;
                }
                catch (Exception ex)
                {
                    sw.Stop();
                    return new StegoResult
                    {
                        Success = false,
                        Message = $"隐写失败: {ex.Message}",
                        ProcessingTime = sw.Elapsed.TotalSeconds,
                        Algorithm = algorithm
                    };
                }
            });
        }

        public async Task<StegoResult> DecodeAsync(string imagePath, string algorithm = "LSB", bool useDecryption = false, bool useDecompression = false, string? decryptionKey = null)
        {
            return await Task.Run(() =>
            {
                var sw = Stopwatch.StartNew();
                
                try
                {
                    if (!File.Exists(imagePath))
                        return new StegoResult 
                        { 
                            Success = false, 
                            Message = "图片文件不存在" 
                        };

                    var image = StegoImage.LoadFromFile(imagePath);
                    
                    StegoResult result;

                    switch (algorithm.ToLower())
                    {
                        case "lsb":
                            result = DecodeLSB(image);
                            break;
                        case "dct":
                            result = new StegoResult 
                            { 
                                Success = false, 
                                Message = "DCT算法需要VIP会员" 
                            };
                            break;
                        default:
                            result = DecodeLSB(image);
                            break;
                    }

                    if (result.Success && !string.IsNullOrEmpty(result.ExtractedText))
                    {
                        try
                        {
                            var dataBytes = System.Convert.FromBase64String(result.ExtractedText);

                            if (useDecompression)
                            {
                                var (decodedData, isValid) = CryptoService.Instance.DecodeWithRedundancy(dataBytes);
                                if (!isValid)
                                {
                                    result.Success = false;
                                    result.Message = "CRC校验失败，数据可能已损坏或抗压缩选项不正确";
                                    return result;
                                }
                                dataBytes = decodedData;
                            }

                            if (useDecryption && !string.IsNullOrEmpty(decryptionKey))
                            {
                                var keyBytes = System.Text.Encoding.UTF8.GetBytes(decryptionKey);
                                if (keyBytes.Length < 32)
                                    Array.Resize(ref keyBytes, 32);
                                dataBytes = CryptoService.Instance.DecryptBytes(dataBytes, keyBytes);
                            }

                            result.ExtractedText = System.Text.Encoding.UTF8.GetString(dataBytes);
                        }
                        catch (Exception ex)
                        {
                            result.Success = false;
                            result.Message = $"数据处理失败: {ex.Message}";
                            return result;
                        }
                    }

                    sw.Stop();
                    result.ProcessingTime = sw.Elapsed.TotalSeconds;
                    result.Algorithm = algorithm;

                    return result;
                }
                catch (Exception ex)
                {
                    sw.Stop();
                    return new StegoResult
                    {
                        Success = false,
                        Message = $"提取失败: {ex.Message}",
                        ProcessingTime = sw.Elapsed.TotalSeconds,
                        Algorithm = algorithm
                    };
                }
            });
        }

        public async Task<StegoResult> EncodeFileAsync(string imagePath, string filePath, string algorithm = "lsb", string? outputPath = null, bool useEncryption = false, bool useRedundancy = false, string? encryptionKey = null)
        {
            return await Task.Run(() =>
            {
                var sw = Stopwatch.StartNew();
                
                try
                {
                    if (!File.Exists(imagePath))
                        return new StegoResult 
                        { 
                            Success = false, 
                            Message = "图片文件不存在" 
                        };

                    if (!File.Exists(filePath))
                        return new StegoResult 
                        { 
                            Success = false, 
                            Message = "要嵌入的文件不存在" 
                        };

                    var image = StegoImage.LoadFromFile(imagePath);
                    var fileBytes = File.ReadAllBytes(filePath);

                    if (useEncryption && !string.IsNullOrEmpty(encryptionKey))
                    {
                        var (encrypted, _) = CryptoService.Instance.EncryptBytes(fileBytes, encryptionKey);
                        fileBytes = encrypted;
                    }

                    if (useRedundancy)
                    {
                        fileBytes = CryptoService.Instance.EncodeWithRedundancy(fileBytes);
                    }
                    
                    if (outputPath == null)
                    {
                        var directory = Path.GetDirectoryName(imagePath);
                        var fileName = Path.GetFileNameWithoutExtension(imagePath);
                        var extension = Path.GetExtension(imagePath);
                        outputPath = Path.Combine(directory ?? "", $"{fileName}_stego{extension}");
                    }

                    StegoResult result;

                    switch (algorithm.ToLower())
                    {
                        case "lsb":
                            result = EncodeFileLSB(image, fileBytes, filePath);
                            break;
                        case "dct":
                            result = new StegoResult 
                            { 
                                Success = false, 
                                Message = "DCT算法需要VIP会员" 
                            };
                            break;
                        default:
                            result = EncodeFileLSB(image, fileBytes, filePath);
                            break;
                    }

                    if (result.Success && result.OutputData != null)
                    {
                        File.WriteAllBytes(outputPath, result.OutputData);
                        result.OutputPath = outputPath;
                    }

                    sw.Stop();
                    result.ProcessingTime = sw.Elapsed.TotalSeconds;
                    result.Algorithm = algorithm;

                    return result;
                }
                catch (Exception ex)
                {
                    sw.Stop();
                    return new StegoResult
                    {
                        Success = false,
                        Message = $"文件嵌入失败: {ex.Message}",
                        ProcessingTime = sw.Elapsed.TotalSeconds,
                        Algorithm = algorithm
                    };
                }
            });
        }

        public async Task<StegoResult> DecodeFileAsync(string imagePath, string algorithm = "LSB")
        {
            return await Task.Run(() =>
            {
                var sw = Stopwatch.StartNew();
                
                try
                {
                    if (!File.Exists(imagePath))
                        return new StegoResult 
                        { 
                            Success = false, 
                            Message = "图片文件不存在" 
                        };

                    var image = StegoImage.LoadFromFile(imagePath);
                    
                    StegoResult result;

                    switch (algorithm.ToLower())
                    {
                        case "lsb":
                            result = DecodeFileLSB(image);
                            break;
                        case "dct":
                            result = new StegoResult 
                            { 
                                Success = false, 
                                Message = "DCT算法需要VIP会员" 
                            };
                            break;
                        default:
                            result = DecodeFileLSB(image);
                            break;
                    }

                    sw.Stop();
                    result.ProcessingTime = sw.Elapsed.TotalSeconds;
                    result.Algorithm = algorithm;

                    return result;
                }
                catch (Exception ex)
                {
                    sw.Stop();
                    return new StegoResult
                    {
                        Success = false,
                        Message = $"文件提取失败: {ex.Message}",
                        ProcessingTime = sw.Elapsed.TotalSeconds,
                        Algorithm = algorithm
                    };
                }
            });
        }

        private StegoResult EncodeLSB(StegoImage image, string data)
        {
            var dataBytes = Encoding.UTF8.GetBytes(data);
            return EncodeLSBFromBytes(image, dataBytes);
        }

        private StegoResult EncodeLSB(StegoImage image, byte[] dataBytes)
        {
            return EncodeLSBFromBytes(image, dataBytes);
        }

        private StegoResult EncodeLSBFromBytes(StegoImage image, byte[] dataBytes)
        {
            try
            {
                var lengthBytes = BitConverter.GetBytes(dataBytes.Length);
                Array.Reverse(lengthBytes);
                var allBytes = lengthBytes.Concat(dataBytes).ToArray();
                
                var maxCapacity = (image.Width * image.Height * 3) / 8;
                if (allBytes.Length > maxCapacity)
                {
                    return new StegoResult
                    {
                        Success = false,
                        Message = $"数据太大，图片容量不足。最大可嵌入: {maxCapacity} 字节，当前数据: {allBytes.Length} 字节"
                    };
                }

                using (var ms = new MemoryStream(image.ImageData))
                using (var bmp = new Bitmap(ms))
                    {
                        int bitIndex = 0;
                        int totalBits = allBytes.Length * 8;

                        for (int y = 0; y < bmp.Height && bitIndex < totalBits; y++)
                        {
                            for (int x = 0; x < bmp.Width && bitIndex < totalBits; x++)
                            {
                                var pixel = bmp.GetPixel(x, y);
                                
                                int r = pixel.R;
                                int g = pixel.G;
                                int b = pixel.B;

                                if (bitIndex < totalBits)
                                {
                                    r = (r & 0xFC) | ((allBytes[bitIndex / 8] >> (6 - (bitIndex % 8))) & 0x03);
                                    bitIndex += 2;
                                }
                                
                                if (bitIndex < totalBits)
                                {
                                    g = (g & 0xFC) | ((allBytes[bitIndex / 8] >> (6 - (bitIndex % 8))) & 0x03);
                                    bitIndex += 2;
                                }
                                
                                if (bitIndex < totalBits)
                                {
                                    b = (b & 0xFC) | ((allBytes[bitIndex / 8] >> (6 - (bitIndex % 8))) & 0x03);
                                    bitIndex += 2;
                                }

                                bmp.SetPixel(x, y, Color.FromArgb(r, g, b));
                            }
                        }

                        using (var outputMs = new MemoryStream())
                        {
                            bmp.Save(outputMs, ImageFormat.Png);
                            return new StegoResult
                            {
                                Success = true,
                                Message = "隐写成功！",
                                OutputData = outputMs.ToArray(),
                                OriginalSize = image.FileSize,
                                OutputSize = outputMs.Length
                            };
                        }
                    }
                }
            catch (Exception ex)
            {
                return new StegoResult
                {
                    Success = false,
                    Message = $"LSB隐写失败: {ex.Message}"
                };
            }
        }

        private StegoResult EncodeFileLSB(StegoImage image, byte[] fileBytes, string originalFilePath)
        {
            try
            {
                var fileName = Path.GetFileName(originalFilePath);
                var fileNameBytes = Encoding.UTF8.GetBytes(fileName);
                var fileNameLengthBytes = BitConverter.GetBytes(fileNameBytes.Length);
                var fileSizeBytes = BitConverter.GetBytes(fileBytes.Length);
                
                var totalHeaderSize = fileNameLengthBytes.Length + fileNameBytes.Length + fileSizeBytes.Length;
                var totalDataSize = totalHeaderSize + fileBytes.Length;
                
                var maxCapacity = (image.Width * image.Height * 3) / 8;
                if (totalDataSize > maxCapacity)
                {
                    return new StegoResult
                    {
                        Success = false,
                        Message = $"文件太大，图片容量不足。最大可嵌入: {maxCapacity} 字节，当前文件: {totalDataSize} 字节"
                    };
                }

                using (var ms = new MemoryStream(image.ImageData))
                using (var bmp = new Bitmap(ms))
                {
                    var allBytes = fileNameLengthBytes.Concat(fileNameBytes).Concat(fileSizeBytes).Concat(fileBytes).ToArray();
                    int bitIndex = 0;
                    int totalBits = allBytes.Length * 8;

                    for (int y = 0; y < bmp.Height && bitIndex < totalBits; y++)
                    {
                        for (int x = 0; x < bmp.Width && bitIndex < totalBits; x++)
                        {
                            var pixel = bmp.GetPixel(x, y);
                            
                            int r = pixel.R;
                            int g = pixel.G;
                            int b = pixel.B;

                            if (bitIndex < totalBits)
                            {
                                r = (r & 0xFE) | ((allBytes[bitIndex / 8] >> (7 - (bitIndex % 8))) & 1);
                                bitIndex++;
                            }
                            
                            if (bitIndex < totalBits)
                            {
                                g = (g & 0xFE) | ((allBytes[bitIndex / 8] >> (7 - (bitIndex % 8))) & 1);
                                bitIndex++;
                            }
                            
                            if (bitIndex < totalBits)
                            {
                                b = (b & 0xFE) | ((allBytes[bitIndex / 8] >> (7 - (bitIndex % 8))) & 1);
                                bitIndex++;
                            }

                            bmp.SetPixel(x, y, Color.FromArgb(r, g, b));
                        }
                    }

                    using (var outputMs = new MemoryStream())
                    {
                        bmp.Save(outputMs, ImageFormat.Png);
                        return new StegoResult
                        {
                            Success = true,
                            Message = $"文件嵌入成功！文件名: {fileName}",
                            OutputData = outputMs.ToArray(),
                            OriginalSize = image.FileSize,
                            OutputSize = outputMs.Length
                        };
                    }
                }
            }
            catch (Exception ex)
            {
                return new StegoResult
                {
                    Success = false,
                    Message = $"文件嵌入失败: {ex.Message}"
                };
            }
        }

        private StegoResult DecodeLSB(StegoImage image)
        {
            try
            {
                using (var ms = new MemoryStream(image.ImageData))
                using (var bmp = new Bitmap(ms))
                {
                    var allBits = new List<int>();

                    for (int y = 0; y < bmp.Height; y++)
                    {
                        for (int x = 0; x < bmp.Width; x++)
                        {
                            var pixel = bmp.GetPixel(x, y);
                            allBits.Add(pixel.R & 3);
                            allBits.Add(pixel.G & 3);
                            allBits.Add(pixel.B & 3);
                        }
                    }

                    if (allBits.Count < 64)
                    {
                        return new StegoResult
                        {
                            Success = false,
                            Message = "图片中没有检测到足够的隐藏数据"
                        };
                    }

                    var lengthBytes = new byte[4];
                    for (int byteIdx = 0; byteIdx < 4; byteIdx++)
                    {
                        for (int bitIdx = 0; bitIdx < 8; bitIdx++)
                        {
                            int bitPos = byteIdx * 8 + bitIdx;
                            if (bitPos < allBits.Count)
                            {
                                if ((allBits[bitPos] & 1) == 1)
                                    lengthBytes[byteIdx] |= (byte)(1 << bitIdx);
                            }
                        }
                    }

                    Array.Reverse(lengthBytes);
                    int dataLength = BitConverter.ToInt32(lengthBytes, 0);
                    
                    if (dataLength <= 0 || dataLength > 1024 * 1024)
                    {
                        return new StegoResult
                        {
                            Success = false,
                            Message = "未检测到有效的文本数据，可能嵌入的是文件，请使用'提取文件'功能"
                        };
                    }

                    var dataBytes = new byte[dataLength];
                    for (int i = 0; i < dataLength; i++)
                    {
                        for (int j = 0; j < 8; j++)
                        {
                            int bitPos = 32 * 8 + i * 8 + j;
                            if (bitPos < allBits.Count)
                            {
                                if ((allBits[bitPos] & 1) == 1)
                                    dataBytes[i] |= (byte)(1 << (7 - j));
                            }
                        }
                    }

                    var extractedText = System.Text.Encoding.UTF8.GetString(dataBytes);

                    return new StegoResult
                    {
                        Success = true,
                        Message = "数据提取成功！",
                        ExtractedText = extractedText
                    };
                }
            }
            catch (Exception ex)
            {
                return new StegoResult
                {
                    Success = false,
                    Message = $"LSB提取失败: {ex.Message}"
                };
            }
        }

        private StegoResult DecodeFileLSB(StegoImage image)
        {
            try
            {
                using (var ms = new MemoryStream(image.ImageData))
                using (var bmp = new Bitmap(ms))
                {
                    var headerBits = new List<bool>();
                    int bitCount = 0;
                    int maxHeaderBits = (4 + 255 + 4) * 8;

                    for (int y = 0; y < bmp.Height && bitCount < maxHeaderBits; y++)
                    {
                        for (int x = 0; x < bmp.Width && bitCount < maxHeaderBits; x++)
                        {
                            var pixel = bmp.GetPixel(x, y);
                            
                            headerBits.Add((pixel.R & 1) == 1);
                            bitCount++;
                            
                            if (bitCount < maxHeaderBits)
                            {
                                headerBits.Add((pixel.G & 1) == 1);
                                bitCount++;
                            }
                            
                            if (bitCount < maxHeaderBits)
                            {
                                headerBits.Add((pixel.B & 1) == 1);
                                bitCount++;
                            }
                        }
                    }

                    if (headerBits.Count < maxHeaderBits)
                    {
                        return new StegoResult
                        {
                            Success = false,
                            Message = "图片中没有检测到嵌入的文件数据"
                        };
                    }

                    var lengthBytes = new byte[4];
                    for (int i = 0; i < 4; i++)
                    {
                        for (int j = 0; j < 8; j++)
                        {
                            int bitIndex = i * 8 + j;
                            if (headerBits[bitIndex])
                                lengthBytes[i] |= (byte)(1 << (7 - j));
                        }
                    }
                    int fileNameLength = BitConverter.ToInt32(lengthBytes, 0);
                    
                    if (fileNameLength <= 0 || fileNameLength > 255)
                    {
                        return new StegoResult
                        {
                            Success = false,
                            Message = "未检测到文件数据，可能是普通文本隐写"
                        };
                    }

                    var fileNameBits = headerBits.Skip(32).Take(fileNameLength * 8).ToList();
                    var fileNameBytes = new byte[fileNameLength];
                    for (int i = 0; i < fileNameLength; i++)
                    {
                        for (int j = 0; j < 8; j++)
                        {
                            int bitIndex = i * 8 + j;
                            if (fileNameBits[bitIndex])
                                fileNameBytes[i] |= (byte)(1 << (7 - j));
                        }
                    }
                    var fileName = Encoding.UTF8.GetString(fileNameBytes);

                    var fileSizeBits = headerBits.Skip(32 + fileNameLength * 8).Take(32).ToList();
                    var fileSizeBytes = new byte[4];
                    for (int i = 0; i < 4; i++)
                    {
                        for (int j = 0; j < 8; j++)
                        {
                            int bitIndex = i * 8 + j;
                            if (fileSizeBits[bitIndex])
                                fileSizeBytes[i] |= (byte)(1 << (7 - j));
                        }
                    }
                    int fileSize = BitConverter.ToInt32(fileSizeBytes, 0);
                    
                    if (fileSize <= 0 || fileSize > 10 * 1024 * 1024)
                    {
                        return new StegoResult
                        {
                            Success = false,
                            Message = "文件大小无效，可能是普通文本隐写"
                        };
                    }

                    int headerEndBit = 32 + fileNameLength * 8 + 32;
                    var dataBits = new List<bool>();
                    int maxDataBits = headerEndBit + fileSize * 8;
                    
                    for (int y = 0; y < bmp.Height; y++)
                    {
                        for (int x = 0; x < bmp.Width; x++)
                        {
                            var pixel = bmp.GetPixel(x, y);
                            
                            dataBits.Add((pixel.R & 1) == 1);
                            if (dataBits.Count >= maxDataBits) break;
                            
                            dataBits.Add((pixel.G & 1) == 1);
                            if (dataBits.Count >= maxDataBits) break;
                            
                            dataBits.Add((pixel.B & 1) == 1);
                            if (dataBits.Count >= maxDataBits) break;
                        }
                        if (dataBits.Count >= maxDataBits) break;
                    }

                    var fileBytes = new byte[fileSize];
                    for (int i = 0; i < fileSize; i++)
                    {
                        for (int j = 0; j < 8; j++)
                        {
                            int bitIndex = headerEndBit + i * 8 + j;
                            if (bitIndex < dataBits.Count && dataBits[bitIndex])
                                fileBytes[i] |= (byte)(1 << (7 - j));
                        }
                    }

                    var decodedData = Convert.ToBase64String(fileBytes);
                    
                    return new StegoResult
                    {
                        Success = true,
                        Message = $"文件提取成功！文件名: {fileName}，大小: {FormatFileSizeLong(fileSize)}",
                        ExtractedText = decodedData,
                        Metadata = fileName
                    };
                }
            }
            catch (Exception ex)
            {
                return new StegoResult
                {
                    Success = false,
                    Message = $"文件提取失败: {ex.Message}"
                };
            }
        }

        private string FormatFileSizeLong(long bytes)
        {
            string[] sizes = { "B", "KB", "MB", "GB" };
            int order = 0;
            double size = bytes;
            while (size >= 1024 && order < sizes.Length - 1)
            {
                order++;
                size = size / 1024;
            }
            return $"{size:0.##} {sizes[order]}";
        }
    }
}
