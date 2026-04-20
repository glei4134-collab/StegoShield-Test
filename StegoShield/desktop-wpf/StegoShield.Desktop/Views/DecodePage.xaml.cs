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
    public partial class DecodePage : UserControl
    {
        private string? _selectedImagePath;
        private string? _extractedData;
        private string? _extractedFileName;
        private byte[]? _extractedFileBytes;
        private bool _isFileMode;

        public DecodePage()
        {
            InitializeComponent();
        }

        private void ChkDecrypt_Changed(object sender, RoutedEventArgs e)
        {
            pnlDecryptKey.Visibility = chkDecrypt.IsChecked == true ? Visibility.Visible : Visibility.Collapsed;
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
                Filter = "图片文件|*.png;*.bmp;*.tiff;*.jpg;*.jpeg|All Files|*.*",
                Title = "选择包含隐藏数据的图片"
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
                _extractedData = null;
                _extractedFileBytes = null;
                _extractedFileName = null;
                _isFileMode = false;

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

        private void CmbAlgorithm_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (cmbAlgorithm == null) return;
            
            if (cmbAlgorithm.SelectedIndex == 2)
            {
                var currentUser = UserService.Instance.CurrentUser;
                if (currentUser == null || !currentUser.IsVip || currentUser.VipExpiry <= DateTime.Now)
                {
                    MessageBox.Show("此算法需要VIP会员权限\n请先在VIP页面激活会员", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                    cmbAlgorithm.SelectedIndex = 0;
                }
            }
        }

        private async void BtnDecode_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_selectedImagePath))
            {
                MessageBox.Show("请先选择图片！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (chkDecrypt.IsChecked == true && string.IsNullOrWhiteSpace(txtDecryptKey.Text))
            {
                MessageBox.Show("请输入解密密钥！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                btnDecode.IsEnabled = false;
                btnDecodeFile.IsEnabled = false;
                progressBar.Visibility = Visibility.Visible;
                progressBar.IsIndeterminate = true;
                txtStatus.Text = "正在提取数据...";
                txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#667EEA"));

                var algorithm = "LSB";
                if (cmbAlgorithm.SelectedIndex == 1)
                {
                    algorithm = "LSB";
                }

                bool useDecryption = chkDecrypt.IsChecked == true;
                bool useDecompression = chkDecompress.IsChecked == true;
                string? decryptionKey = useDecryption ? txtDecryptKey.Text : null;

                var result = await StegoService.Instance.DecodeAsync(_selectedImagePath, algorithm, useDecryption, useDecompression, decryptionKey);

                progressBar.Visibility = Visibility.Collapsed;

                if (result.Success)
                {
                    _extractedData = result.ExtractedText;
                    _isFileMode = false;
                    _extractedFileBytes = null;
                    txtStatus.Text = $"✅ 提取成功！处理时间: {result.ProcessingTime:F2}秒";
                    txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34C759"));
                    MessageBox.Show("提取成功！\n\n提取的数据：\n" + (_extractedData?.Length > 100 ? _extractedData?.Substring(0, 100) + "..." : _extractedData), "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    _extractedData = null;
                    txtStatus.Text = $"❌ 提取失败: {result.Message}";
                    txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3B30"));
                }
            }
            catch (Exception ex)
            {
                progressBar.Visibility = Visibility.Collapsed;
                txtStatus.Text = $"❌ 发生错误: {ex.Message}";
                txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3B30"));
            }
            finally
            {
                btnDecode.IsEnabled = true;
                btnDecodeFile.IsEnabled = true;
            }
        }

        private void BtnCopy_Click(object sender, RoutedEventArgs e)
        {
            if (_isFileMode && _extractedFileBytes != null)
            {
                MessageBox.Show("请使用'保存文件'按钮保存文件！", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }

            if (!string.IsNullOrEmpty(_extractedData))
            {
                Clipboard.SetText(_extractedData);
                MessageBox.Show("已复制到剪贴板！", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            else
            {
                MessageBox.Show("没有可复制的数据！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private void BtnSave_Click(object sender, RoutedEventArgs e)
        {
            if (_isFileMode && _extractedFileBytes != null)
            {
                SaveExtractedFile();
            }
            else if (!string.IsNullOrEmpty(_extractedData))
            {
                var dialog = new SaveFileDialog
                {
                    Filter = "文本文件|*.txt|所有文件|*.*",
                    Title = "保存提取结果",
                    FileName = "extracted_data.txt"
                };

                if (dialog.ShowDialog() == true)
                {
                    try
                    {
                        File.WriteAllText(dialog.FileName, _extractedData);
                        MessageBox.Show($"已保存到: {dialog.FileName}", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"保存失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }
            }
            else
            {
                MessageBox.Show("没有可保存的数据！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
            }
        }

        private async void BtnDecodeFile_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_selectedImagePath))
            {
                MessageBox.Show("请先选择图片！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                btnDecode.IsEnabled = false;
                btnDecodeFile.IsEnabled = false;
                progressBar.Visibility = Visibility.Visible;
                progressBar.IsIndeterminate = true;
                txtStatus.Text = "正在提取文件...";
                txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#667EEA"));

                var algorithm = "LSB";
                var result = await StegoService.Instance.DecodeFileAsync(_selectedImagePath, algorithm);

                progressBar.Visibility = Visibility.Collapsed;

                if (result.Success)
                {
                    _isFileMode = true;
                    _extractedFileName = result.Metadata;
                    
                    if (!string.IsNullOrEmpty(result.ExtractedText))
                    {
                        try
                        {
                            _extractedFileBytes = Convert.FromBase64String(result.ExtractedText);
                        }
                        catch
                        {
                            _extractedFileBytes = null;
                        }
                    }

                    if (_extractedFileBytes != null)
                    {
                        txtStatus.Text = $"✅ 文件提取成功！文件名: {_extractedFileName}，大小: {FormatFileSize(_extractedFileBytes.Length)}";
                        txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#34C759"));
                    }
                    else
                    {
                        _extractedFileBytes = null;
                        txtStatus.Text = $"⚠️ {result.Message}";
                        txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF9500"));
                        MessageBox.Show(result.Message, "提示", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                }
                else
                {
                    _isFileMode = false;
                    _extractedFileName = null;
                    _extractedFileBytes = null;
                    txtStatus.Text = $"❌ 提取失败: {result.Message}";
                    txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3B30"));
                }
            }
            catch (Exception ex)
            {
                progressBar.Visibility = Visibility.Collapsed;
                txtStatus.Text = $"❌ 发生错误: {ex.Message}";
                txtStatus.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#FF3B30"));
            }
            finally
            {
                btnDecode.IsEnabled = true;
                btnDecodeFile.IsEnabled = true;
            }
        }

        private void SaveExtractedFile()
        {
            if (_extractedFileBytes == null || string.IsNullOrEmpty(_extractedFileName))
            {
                MessageBox.Show("没有可保存的文件！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var dialog = new SaveFileDialog
            {
                Filter = "所有文件|*.*",
                Title = "保存提取的文件",
                FileName = _extractedFileName
            };

            if (dialog.ShowDialog() == true)
            {
                try
                {
                    File.WriteAllBytes(dialog.FileName, _extractedFileBytes);
                    MessageBox.Show($"文件已保存到: {dialog.FileName}", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"保存失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                }
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
