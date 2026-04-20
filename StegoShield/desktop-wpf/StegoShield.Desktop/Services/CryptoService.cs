using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;

namespace StegoShield.Desktop.Services
{
    public class CryptoService
    {
        private static readonly Lazy<CryptoService> _instance = 
            new Lazy<CryptoService>(() => new CryptoService());
        
        public static CryptoService Instance => _instance.Value;

        private readonly string _keyFilePath;
        private byte[] _encryptionKey;
        private byte[] _encryptionIV;

        private CryptoService()
        {
            var appDataPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "StegoShield"
            );
            Directory.CreateDirectory(appDataPath);
            _keyFilePath = Path.Combine(appDataPath, ".keystore");

            LoadOrGenerateKeys();
        }

        private void LoadOrGenerateKeys()
        {
            try
            {
                if (File.Exists(_keyFilePath))
                {
                    var encryptedData = File.ReadAllBytes(_keyFilePath);
                    var keyData = ProtectedData.Unprotect(
                        encryptedData,
                        null,
                        DataProtectionScope.CurrentUser
                    );

                    var parts = Encoding.UTF8.GetString(keyData).Split('|');
                    _encryptionKey = Convert.FromBase64String(parts[0]);
                    _encryptionIV = Convert.FromBase64String(parts[1]);
                }
                else
                {
                    GenerateNewKeys();
                }
            }
            catch
            {
                GenerateNewKeys();
            }
        }

        private void GenerateNewKeys()
        {
            using (var aes = Aes.Create())
            {
                aes.GenerateKey();
                aes.GenerateIV();
                _encryptionKey = aes.Key;
                _encryptionIV = aes.IV;
            }

            var keyData = $"{Convert.ToBase64String(_encryptionKey)}|{Convert.ToBase64String(_encryptionIV)}";
            var encryptedData = ProtectedData.Protect(
                Encoding.UTF8.GetBytes(keyData),
                null,
                DataProtectionScope.CurrentUser
            );
            File.WriteAllBytes(_keyFilePath, encryptedData);
        }

        public string Encrypt(string plainText)
        {
            if (string.IsNullOrEmpty(plainText))
                return string.Empty;

            try
            {
                using (var aes = Aes.Create())
                {
                    aes.Key = _encryptionKey;
                    aes.IV = _encryptionIV;
                    aes.Mode = CipherMode.CBC;
                    aes.Padding = PaddingMode.PKCS7;

                    using (var encryptor = aes.CreateEncryptor())
                    using (var msEncrypt = new MemoryStream())
                    using (var csEncrypt = new CryptoStream(msEncrypt, encryptor, CryptoStreamMode.Write))
                    using (var swEncrypt = new StreamWriter(csEncrypt))
                    {
                        swEncrypt.Write(plainText);
                        swEncrypt.Flush();
                        csEncrypt.FlushFinalBlock();
                        return Convert.ToBase64String(msEncrypt.ToArray());
                    }
                }
            }
            catch (Exception ex)
            {
                throw new CryptographicException($"加密失败: {ex.Message}", ex);
            }
        }

        public string Decrypt(string cipherText)
        {
            if (string.IsNullOrEmpty(cipherText))
                return string.Empty;

            try
            {
                using (var aes = Aes.Create())
                {
                    aes.Key = _encryptionKey;
                    aes.IV = _encryptionIV;
                    aes.Mode = CipherMode.CBC;
                    aes.Padding = PaddingMode.PKCS7;

                    using (var decryptor = aes.CreateDecryptor())
                    using (var msDecrypt = new MemoryStream(Convert.FromBase64String(cipherText)))
                    using (var csDecrypt = new CryptoStream(msDecrypt, decryptor, CryptoStreamMode.Read))
                    using (var srDecrypt = new StreamReader(csDecrypt))
                    {
                        return srDecrypt.ReadToEnd();
                    }
                }
            }
            catch (Exception ex)
            {
                throw new CryptographicException($"解密失败: {ex.Message}", ex);
            }
        }

        public string HashPassword(string password)
        {
            if (string.IsNullOrEmpty(password))
                throw new ArgumentNullException(nameof(password));

            using (var sha256 = SHA256.Create())
            {
                var saltedPassword = $"StegoShield_{password}_Salt";
                var hashedBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(saltedPassword));
                return Convert.ToBase64String(hashedBytes);
            }
        }

        public bool VerifyPassword(string password, string hash)
        {
            if (string.IsNullOrEmpty(password) || string.IsNullOrEmpty(hash))
                return false;

            var computedHash = HashPassword(password);
            return computedHash == hash;
        }

        public string EncryptObject<T>(T obj)
        {
            var json = JsonConvert.SerializeObject(obj);
            return Encrypt(json);
        }

        public T? DecryptObject<T>(string cipherText)
        {
            var json = Decrypt(cipherText);
            return JsonConvert.DeserializeObject<T>(json);
        }

        public string GenerateRandomKey(int length = 32)
        {
            using (var rng = RandomNumberGenerator.Create())
            {
                var randomBytes = new byte[length];
                rng.GetBytes(randomBytes);
                return Convert.ToBase64String(randomBytes);
            }
        }

        public string GenerateApiKey(string prefix = "sk_stego_")
        {
            var key = GenerateRandomKey(32);
            return $"{prefix}{key.Replace("+", "").Replace("/", "").Replace("=", "")}";
        }

        public (byte[] EncryptedData, byte[] Key) EncryptBytes(byte[] plainData, string? keyString = null)
        {
            byte[] key;
            if (string.IsNullOrEmpty(keyString))
            {
                using (var rng = RandomNumberGenerator.Create())
                {
                    key = new byte[32];
                    rng.GetBytes(key);
                }
            }
            else
            {
                var keyBytes = Encoding.UTF8.GetBytes(keyString);
                if (keyBytes.Length < 32)
                    Array.Resize(ref keyBytes, 32);
                else if (keyBytes.Length > 32)
                    Array.Resize(ref keyBytes, 32);
                key = keyBytes;
            }

            using (var aes = Aes.Create())
            {
                aes.Key = key;
                aes.GenerateIV();
                aes.Mode = CipherMode.CBC;
                aes.Padding = PaddingMode.PKCS7;

                using (var encryptor = aes.CreateEncryptor())
                using (var msEncrypt = new MemoryStream())
                {
                    using (var csEncrypt = new CryptoStream(msEncrypt, encryptor, CryptoStreamMode.Write))
                    {
                        csEncrypt.Write(plainData, 0, plainData.Length);
                        csEncrypt.FlushFinalBlock();
                    }
                    
                    var iv = aes.IV;
                    var encrypted = msEncrypt.ToArray();
                    var result = new byte[iv.Length + encrypted.Length];
                    Buffer.BlockCopy(iv, 0, result, 0, iv.Length);
                    Buffer.BlockCopy(encrypted, 0, result, iv.Length, encrypted.Length);
                    return (result, key);
                }
            }
        }

        public byte[] DecryptBytes(byte[] encryptedData, byte[] key)
        {
            if (encryptedData.Length < 16)
                throw new CryptographicException("加密数据长度无效");

            var iv = new byte[16];
            var ciphertext = new byte[encryptedData.Length - 16];
            Buffer.BlockCopy(encryptedData, 0, iv, 0, 16);
            Buffer.BlockCopy(encryptedData, 16, ciphertext, 0, ciphertext.Length);

            using (var aes = Aes.Create())
            {
                aes.Key = key;
                aes.IV = iv;
                aes.Mode = CipherMode.CBC;
                aes.Padding = PaddingMode.PKCS7;

                using (var decryptor = aes.CreateDecryptor())
                using (var msDecrypt = new MemoryStream(ciphertext))
                using (var csDecrypt = new CryptoStream(msDecrypt, decryptor, CryptoStreamMode.Read))
                using (var msOutput = new MemoryStream())
                {
                    csDecrypt.CopyTo(msOutput);
                    return msOutput.ToArray();
                }
            }
        }

        public byte[] EncodeWithRedundancy(byte[] payload, int redundancy = 3)
        {
            var result = new System.Collections.Generic.List<byte>();
            
            foreach (var b in payload)
            {
                for (int i = 7; i >= 0; i--)
                {
                    byte bit = (byte)((b >> i) & 1);
                    for (int r = 0; r < redundancy; r++)
                    {
                        result.Add(bit);
                    }
                }
            }

            var crc = Crc32(payload);
            var crcBytes = BitConverter.GetBytes(crc);
            result.AddRange(crcBytes);

            return result.ToArray();
        }

        public (byte[] Payload, bool IsValid) DecodeWithRedundancy(byte[] encodedPayload, int redundancy = 3)
        {
            if (encodedPayload.Length < 4)
                return (Array.Empty<byte>(), false);

            var totalBits = encodedPayload.Length - 4;
            if (totalBits < 0 || totalBits % redundancy != 0)
                return (Array.Empty<byte>(), false);

            var dataBits = totalBits / redundancy * redundancy;

            var storedCrc = BitConverter.ToUInt32(encodedPayload, dataBits);

            var result = new System.Collections.Generic.List<byte>();
            for (int i = 0; i < dataBits; i += redundancy)
            {
                int sum = 0;
                for (int r = 0; r < redundancy; r++)
                {
                    sum += encodedPayload[i + r];
                }
                byte bit = (byte)(sum > redundancy / 2 ? 1 : 0);
                result.Add(bit);
            }

            var payloadBytes = BitsToBytes(result.ToArray());

            var calculatedCrc = Crc32(payloadBytes);
            bool isValid = calculatedCrc == storedCrc;

            return (payloadBytes, isValid);
        }

        private byte[] BitsToBytes(byte[] bits)
        {
            var result = new System.Collections.Generic.List<byte>();
            for (int i = 0; i + 8 <= bits.Length; i += 8)
            {
                byte b = 0;
                for (int j = 0; j < 8; j++)
                {
                    if (bits[i + j] == 1)
                        b |= (byte)(1 << (7 - j));
                }
                result.Add(b);
            }
            return result.ToArray();
        }

        private uint Crc32(byte[] data)
        {
            uint crc = 0xFFFFFFFF;
            var table = GetCrc32Table();
            
            foreach (var b in data)
            {
                crc = (crc >> 8) ^ table[(crc ^ b) & 0xFF];
            }
            
            return crc ^ 0xFFFFFFFF;
        }

        private static uint[] _crc32Table;
        private static uint[] GetCrc32Table()
        {
            if (_crc32Table == null)
            {
                _crc32Table = new uint[256];
                for (int i = 0; i < 256; i++)
                {
                    uint c = (uint)i;
                    for (int j = 0; j < 8; j++)
                    {
                        c = (c & 1) != 0 ? (0xEDB88320 ^ (c >> 1)) : (c >> 1);
                    }
                    _crc32Table[i] = c;
                }
            }
            return _crc32Table;
        }
    }
}
