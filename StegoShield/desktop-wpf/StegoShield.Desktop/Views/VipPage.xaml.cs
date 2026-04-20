using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using StegoShield.Desktop.Services;

namespace StegoShield.Desktop.Views
{
    public partial class VipPage : UserControl
    {
        public VipPage()
        {
            InitializeComponent();
            UpdateVipStatus();
            UpdateServerStatus();
            
            HttpServerService.Instance.StatusChanged += OnServerStatusChanged;
        }

        private void OnServerStatusChanged(object? sender, HttpServerService.ServerStatusEventArgs e)
        {
            Dispatcher.Invoke(() => UpdateServerStatus());
        }

        private void UpdateVipStatus()
        {
            var user = UserService.Instance.CurrentUser;
            if (user != null)
            {
                if (user.IsVip && user.VipExpiry.HasValue && user.VipExpiry.Value > DateTime.Now)
                {
                    txtVipStatus.Text = "当前状态: VIP会员";
                    txtVipExpiry.Text = $"到期时间: {user.VipExpiry.Value:yyyy-MM-dd}";
                    txtActivationCode.IsEnabled = false;
                    btnActivate.Content = "已激活";
                    btnActivate.IsEnabled = false;
                    serverPanel.Visibility = Visibility.Visible;
                    UpdateApiKeysList();
                }
                else
                {
                    txtVipStatus.Text = "当前状态: 标准版";
                    txtVipExpiry.Text = "输入激活码解锁VIP特权";
                    txtActivationCode.IsEnabled = true;
                    btnActivate.Content = "激活VIP";
                    btnActivate.IsEnabled = true;
                    serverPanel.Visibility = Visibility.Collapsed;
                }
            }
            else
            {
                txtVipStatus.Text = "当前状态: 未登录";
                txtVipExpiry.Text = "请先登录";
                txtActivationCode.IsEnabled = false;
                btnActivate.Content = "请先登录";
                btnActivate.IsEnabled = false;
                serverPanel.Visibility = Visibility.Collapsed;
            }
        }

        private void UpdateServerStatus()
        {
            if (HttpServerService.Instance.IsRunning)
            {
                txtServerStatus.Text = "🟢 运行中";
                txtServerStatus.Foreground = new SolidColorBrush(Color.FromRgb(39, 174, 96));
                txtServerUrl.Text = $"http://localhost:{HttpServerService.Instance.Port}/api/v1/";
                btnStartStop.Content = "⏹ 停止服务器";
                btnStartStop.IsEnabled = true;
            }
            else
            {
                txtServerStatus.Text = "⚫ 已停止";
                txtServerStatus.Foreground = new SolidColorBrush(Color.FromRgb(128, 128, 128));
                txtServerUrl.Text = "服务器未启动";
                btnStartStop.Content = "▶ 启动服务器";
                btnStartStop.IsEnabled = true;
            }
        }

        private void UpdateApiKeysList()
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                apiKeysList.ItemsSource = null;
                return;
            }

            var keys = UserService.Instance.GetApiKeys();
            apiKeysList.ItemsSource = keys;
        }

        private async void BtnActivate_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var code = txtActivationCode.Text.Trim();
            if (string.IsNullOrEmpty(code))
            {
                MessageBox.Show("请输入激活码！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                txtActivationCode.Focus();
                return;
            }

            btnActivate.IsEnabled = false;
            btnActivate.Content = "验证中...";

            try
            {
                var result = await ActivationService.Instance.ValidateActivationCodeAsync(code);

                if (result.Success)
                {
                    var expiryDate = DateTime.Now.AddDays(result.VipDays);
                    var activateResult = await UserService.Instance.ActivateVipAsync(expiryDate);

                    if (activateResult.Success)
                    {
                        ActivationService.Instance.SaveActivationCache(code, result.VipDays, expiryDate);
                        
                        MessageBox.Show(
                            $"🎉 {result.Message}\n\n到期时间：{expiryDate:yyyy年MM月dd日}\n\nVIP功能已激活，可以离线使用！",
                            "激活成功",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information);

                        txtActivationCode.Clear();
                        UpdateVipStatus();
                    }
                    else
                    {
                        MessageBox.Show($"激活失败：{activateResult.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }
                else
                {
                    MessageBox.Show(result.Message, "激活失败", MessageBoxButton.OK, MessageBoxImage.Warning);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"激活失败：{ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                btnActivate.IsEnabled = true;
                btnActivate.Content = "激活VIP";
            }
        }

        private void BtnStartStop_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (!UserService.Instance.IsVip())
            {
                MessageBox.Show("VIP会员才能启动API服务器！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (HttpServerService.Instance.IsRunning)
            {
                HttpServerService.Instance.StopServer();
            }
            else
            {
                _ = HttpServerService.Instance.StartServerAsync();
            }
        }

        private async void BtnCreateApiKey_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (!UserService.Instance.IsVip())
            {
                MessageBox.Show("VIP会员才能创建API密钥！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            try
            {
                var keyName = $"Key_{DateTime.Now:yyyyMMdd_HHmmss}";
                var key = UserService.Instance.CreateApiKey(keyName);
                
                UpdateApiKeysList();
                
                Clipboard.SetText(key.Key);
                MessageBox.Show($"API密钥已创建并复制到剪贴板！\n\n密钥名称: {key.Name}\n密钥: {key.Key}\n\n⚠️ 请妥善保存密钥，它只会显示一次！", 
                    "成功", MessageBoxButton.OK, MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"创建API密钥失败: {ex.Message}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void BtnDeleteKey_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string keyId)
            {
                var result = MessageBox.Show(
                    "确定要删除此API密钥吗？删除后，使用该密钥的应用程序将无法访问API。",
                    "确认删除",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Warning);

                if (result == MessageBoxResult.Yes)
                {
                    if (UserService.Instance.DeleteApiKey(keyId))
                    {
                        UpdateApiKeysList();
                        MessageBox.Show("API密钥已删除", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
                    }
                    else
                    {
                        MessageBox.Show("删除API密钥失败", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
                    }
                }
            }
        }

        private void BtnCopyKey_Click(object sender, RoutedEventArgs e)
        {
            if (sender is Button btn && btn.Tag is string key)
            {
                Clipboard.SetText(key);
                MessageBox.Show("API密钥已复制到剪贴板！", "成功", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }
    }
}
