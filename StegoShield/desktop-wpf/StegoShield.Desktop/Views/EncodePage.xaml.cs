using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using Forms = System.Windows.Forms;
using StegoShield.Desktop.Models;
using StegoShield.Desktop.Services;

namespace StegoShield.Desktop.Views
{
    public partial class EncodePage : System.Windows.Controls.UserControl
    {
        private string? _selectedImagePath;
        private string? _selectedFilePath;
        private long _selectedFileSize;
        
        private const long MaxFileSize = 10 * 1024 * 1024; // 10MB limit for embedded file

        public EncodePage()
        {
            InitializeComponent();
            SetDefaultOutputPath();
            chkEncrypt.Checked += ChkEncrypt_Changed;
            chkEncrypt.Unchecked += ChkEncrypt_Changed;
        }

        private void ChkEncrypt_Changed(object sender, RoutedEventArgs e)
        {
            pnlEncryptionKey.Visibility = chkEncrypt.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
            if (chkEncrypt.IsChecked == true && string.IsNullOrEmpty(txtEncryptionKey.Text))
            {
                txtEncryptionKey.Text = GenerateKey();
            }
        }

        private string GenerateKey()
        {
            return CryptoService.Instance.GenerateRandomKey(32).Replace("+", "").Replace("/", "").Replace("=", "");
        }

        private void BtnGenerateKey_Click(object sender, RoutedEventArgs e)
        {
            txtEncryptionKey.Text = GenerateKey();
        }

        private void SetDefaultOutputPath()
        {
            var documentsPath = Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
            var outputDir = Path.Combine(documentsPath, "StegoShield", "Output");
            Directory.CreateDirectory(outputDir);
            txtOutputPath.Text = outputDir;
        }

        private void ImageDropZone_Click(object sender, MouseButtonEventArgs e)
        {
            SelectImage();
        }

        private void ImageDropZone_Drop(object sender, DragEventArgs e)
        {
            imageDropZone.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DEE2E6"));

            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);
                if (files.Length > 0)
                {
                    ProcessImageFile(files[0]);
                }
            }
        }

        private void ImageDropZone_DragEnter(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                imageDropZone.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#667EEA"));
                e.Effects = DragDropEffects.Copy;
            }
            else
            {
                e.Effects = DragDropEffects.None;
            }
            e.Handled = true;
        }

        private void ImageDropZone_DragLeave(object sender, DragEventArgs e)
        {
            imageDropZone.BorderBrush = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#DEE2E6"));
        }

        private void SelectImage()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "图片文件|*.png;*.bmp;*.tiff;*.jpg;*.jpeg|PNG图片|*.png|BMP图片|*.bmp|TIFF图片|*.tiff|JPEG图片|*.jpg;*.jpeg|All Files|*.*",
                Title = "选择图片"
            };

            if (dialog.ShowDialog() == true)
            {
                ProcessImageFile(dialog.FileName);
            }
        }

        private void ProcessImageFile(string filePath)
        {
            if (File.Exists(filePath))
            {
                _selectedImagePath = filePath;
                txtImagePath.Text = filePath;
                txtDropHint.Text = "已选择图片";

                try
                {
                    var bitmap = new BitmapImage();
                    bitmap.BeginInit();
                    bitmap.UriSource = new Uri(filePath);
                    bitmap.CacheOption = BitmapCacheOption.OnLoad;
                    bitmap.EndInit();
                    bitmap.Freeze();

                    imageDropZone.Background = new ImageBrush
                    {
                        ImageSource = bitmap,
                        Stretch = Stretch.Uniform
                    };
                }
                catch
                {
                    imageDropZone.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#F8F9FA"));
                }
            }
        }

        private void FileDropZone_Click(object sender, MouseButtonEventArgs e)
        {
            SelectFile();
        }

        private void SelectFile()
        {
            var dialog = new OpenFileDialog
            {
                Filter = "所有文件|*.*|文本文件|*.txt|文档文件|*.doc;*.docx|压缩文件|*.zip;*.rar|图片文件|*.png;*.jpg;*.bmp",
                Title = "选择要隐藏的文件"
            };

            if (dialog.ShowDialog() == true)
            {
                ProcessSelectedFile(dialog.FileName);
            }
        }

        public void ProcessSelectedFile(string filePath)
        {
            if (File.Exists(filePath))
            {
                var fileInfo = new FileInfo(filePath);
                _selectedFileSize = fileInfo.Length;
                
                if (_selectedFileSize > MaxFileSize)
                {
                    MessageBox.Show($"文件太大！最大支持 {FormatFileSize(MaxFileSize)} 的文件", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
                
                _selectedFilePath = filePath;
                txtFileName.Text = fileInfo.Name;
                txtFileSize.Text = $"大小: {FormatFileSize(_selectedFileSize)}";
                txtFileHint.Text = "已选择文件，可直接拖放覆盖";
            }
        }

        private void CmbAlgorithm_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (txtAlgorithmInfo == null) return;
            
            if (cmbAlgorithm.SelectedIndex == 0)
            {
                txtAlgorithmInfo.Text = "最基础的隐写算法，将数据嵌入到图片像素的最低位";
            }
            else if (cmbAlgorithm.SelectedIndex == 1)
            {
                var currentUser = UserService.Instance.CurrentUser;
                if (currentUser != null && currentUser.IsVip && currentUser.VipExpiry > DateTime.Now)
                {
                    txtAlgorithmInfo.Text = "适合JPEG格式的高级隐写算法";
                }
                else
                {
                    txtAlgorithmInfo.Text = "此算法需要VIP会员权限";
                    MessageBox.Show("此算法需要VIP会员权限\n请先在VIP页面激活会员", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                    cmbAlgorithm.SelectedIndex = 0;
                }
            }
        }

        private void BtnBrowse_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Forms.FolderBrowserDialog
            {
                Description = "选择输出目录",
                ShowNewFolderButton = true
            };

            if (dialog.ShowDialog() == Forms.DialogResult.OK)
            {
                txtOutputPath.Text = dialog.SelectedPath;
            }
        }

        private async void BtnEncode_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_selectedImagePath))
            {
                MessageBox.Show("请先选择图片！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            bool isFileMode = dataTabControl.SelectedIndex == 1;
            
            if (isFileMode)
            {
                if (string.IsNullOrEmpty(_selectedFilePath))
                {
                    MessageBox.Show("请先选择要隐藏的文件！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }
            else
            {
                if (string.IsNullOrWhiteSpace(txtData.Text))
                {
                    MessageBox.Show("请输入要隐藏的数据！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                    return;
                }
            }

            if (chkEncrypt.IsChecked == true && string.IsNullOrWhiteSpace(txtEncryptionKey.Text))
            {
                MessageBox.Show("请输入加密密钥！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                btnEncode.IsEnabled = false;
                progressBar.Visibility = Visibility.Visible;
                progressBar.IsIndeterminate = true;
                txtResult.Text = isFileMode ? "正在嵌入文件..." : "正在处理...";
                txtResult.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#667EEA"));

                var algorithm = "LSB";
                var outputDir = txtOutputPath.Text;
                var fileName = Path.GetFileNameWithoutExtension(_selectedImagePath);
                var extension = Path.GetExtension(_selectedImagePath);
                var outputPath = Path.Combine(outputDir, $"{fileName}_stego{extension}");

                bool useEncryption = chkEncrypt.IsChecked == true;
                bool useRedundancy = chkCompress.IsChecked == true;
                string? encryptionKey = useEncryption ? txtEncryptionKey.Text : null;

                StegoResult result;
                
                if (isFileMode)
                {
                    result = await StegoService.Instance.EncodeFileAsync(_selectedImagePath, _selectedFilePath!, algorithm, outputPath, useEncryption, useRedundancy, encryptionKey);
                }
                else
                {
                    result = await StegoService.Instance.EncodeAsync(_selectedImagePath, txtData.Text, algorithm, outputPath, useEncryption, useRedundancy, encryptionKey);
                }

                progressBar.Visibility = Visibility.Collapsed;

                var modeText = isFileMode ? "文件嵌入" : "隐写";

                if (result.Success)
                {
                    var extraInfo = useEncryption ? $"\n🔐 加密密钥: {encryptionKey}" : "";
                    txtResult.Text = $"✅ {modeText}成功！\n输出文件: {result.OutputPath}\n处理时间: {result.ProcessingTime:F2}秒\n原始大小: {FormatFileSize(result.OriginalSize)}\n输出大小: {FormatFileSize(result.OutputSize)}{extraInfo}";
                    txtResult.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34C759"));
                    MessageBox.Show($"{modeText}成功！\n文件已保存到: {result.OutputPath}{extraInfo}", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    txtResult.Text = $"❌ {modeText}失败: {result.Message}";
                    txtResult.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3B30"));
                }
            }
            catch (Exception ex)
            {
                progressBar.Visibility = Visibility.Collapsed;
                txtResult.Text = $"❌ 发生错误: {ex.Message}";
                txtResult.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3B30"));
            }
            finally
            {
                btnEncode.IsEnabled = true;
            }
        }

        private string FormatFileSize(long bytes)
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
