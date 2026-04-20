using System;
using System.Windows;
using System.Windows.Controls;
using Forms = System.Windows.Forms;
using StegoShield.Desktop.Models;
using StegoShield.Desktop.Services;

namespace StegoShield.Desktop.Views
{
    public partial class SettingsPage : System.Windows.Controls.UserControl
    {
        public SettingsPage()
        {
            InitializeComponent();
            LoadSettings();
        }

        private void LoadSettings()
        {
            var user = UserService.Instance.CurrentUser;
            if (user != null)
            {
                txtUsername.Text = user.Username;
                txtEmail.Text = user.Email;

                if (user.Settings != null)
                {
                    txtDefaultPath.Text = user.Settings.DefaultOutputPath;
                    sliderQuality.Value = user.Settings.ImageQuality;
                    txtQuality.Text = $"{user.Settings.ImageQuality}%";
                    chkKeepBackup.IsChecked = user.Settings.KeepBackup;
                    chkNotifications.IsChecked = user.Settings.EnableNotifications;
                    chkSound.IsChecked = user.Settings.EnableSound;
                }
            }
            else
            {
                txtUsername.Text = "未登录";
                txtEmail.Text = "未绑定";
            }
        }

        private void BtnChangeEmail_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var dialog = new InputDialog("修改邮箱", "请输入新邮箱地址:");
            if (dialog.ShowDialog() == true && !string.IsNullOrWhiteSpace(dialog.InputText))
            {
                var result = UserService.Instance.UpdateEmailAsync(dialog.InputText).Result;
                MessageBox.Show(result.Message, "结果", MessageBoxButton.OK, 
                    result.Success ? MessageBoxImage.Information : MessageBoxImage.Warning);

                if (result.Success)
                {
                    txtEmail.Text = dialog.InputText;
                }
            }
        }

        private void BtnChangePassword_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var oldPwdDialog = new InputDialog("修改密码", "请输入原密码:");
            if (oldPwdDialog.ShowDialog() == true)
            {
                var newPwdDialog = new InputDialog("修改密码", "请输入新密码:");
                if (newPwdDialog.ShowDialog() == true)
                {
                    var result = UserService.Instance.UpdatePasswordAsync(oldPwdDialog.InputText, newPwdDialog.InputText).Result;
                    MessageBox.Show(result.Message, "结果", MessageBoxButton.OK,
                        result.Success ? MessageBoxImage.Information : MessageBoxImage.Warning);
                }
            }
        }

        private void BtnBrowseDefault_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new Forms.FolderBrowserDialog
            {
                Description = "选择默认输出目录",
                ShowNewFolderButton = true
            };

            if (dialog.ShowDialog() == Forms.DialogResult.OK)
            {
                txtDefaultPath.Text = dialog.SelectedPath;
            }
        }

        private async void BtnSaveSettings_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录以保存设置！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            var settings = new UserSettings
            {
                DefaultOutputPath = txtDefaultPath.Text,
                ImageQuality = (int)sliderQuality.Value,
                KeepBackup = chkKeepBackup.IsChecked ?? true,
                EnableNotifications = chkNotifications.IsChecked ?? true,
                EnableSound = chkSound.IsChecked ?? true
            };

            var result = await UserService.Instance.UpdateSettingsAsync(settings);
            MessageBox.Show(result.Message, "结果", MessageBoxButton.OK,
                result.Success ? MessageBoxImage.Information : MessageBoxImage.Warning);
        }

        private void BtnStartServer_Click(object sender, RoutedEventArgs e)
        {
            if (!UserService.Instance.IsLoggedIn)
            {
                MessageBox.Show("请先登录！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            if (!UserService.Instance.IsVip())
            {
                MessageBox.Show("VIP会员才能使用服务器模式！", "提示", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            MessageBox.Show("服务器功能开发中...", "提示", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    public class InputDialog : Window
    {
        private System.Windows.Controls.TextBox _textBox;
        public string InputText => _textBox.Text;

        public InputDialog(string title, string prompt)
        {
            Title = title;
            Width = 400;
            Height = 150;
            WindowStartupLocation = WindowStartupLocation.CenterOwner;
            ResizeMode = ResizeMode.NoResize;

            var grid = new System.Windows.Controls.Grid();
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition { Height = System.Windows.GridLength.Auto });
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition { Height = System.Windows.GridLength.Auto });
            grid.RowDefinitions.Add(new System.Windows.Controls.RowDefinition { Height = System.Windows.GridLength.Auto });
            grid.Margin = new Thickness(20);

            var label = new System.Windows.Controls.TextBlock
            {
                Text = prompt,
                Margin = new Thickness(0, 0, 0, 10)
            };
            System.Windows.Controls.Grid.SetRow(label, 0);
            grid.Children.Add(label);

            _textBox = new System.Windows.Controls.TextBox
            {
                Margin = new Thickness(0, 0, 0, 20),
                Padding = new Thickness(8)
            };
            System.Windows.Controls.Grid.SetRow(_textBox, 1);
            grid.Children.Add(_textBox);

            var buttonPanel = new System.Windows.Controls.StackPanel
            {
                Orientation = System.Windows.Controls.Orientation.Horizontal,
                HorizontalAlignment = HorizontalAlignment.Right
            };
            System.Windows.Controls.Grid.SetRow(buttonPanel, 2);

            var okButton = new System.Windows.Controls.Button
            {
                Content = "确定",
                Width = 80,
                Margin = new Thickness(0, 0, 10, 0),
                Padding = new Thickness(10, 5, 10, 5)
            };
            okButton.Click += (s, e) => { DialogResult = true; Close(); };
            buttonPanel.Children.Add(okButton);

            var cancelButton = new System.Windows.Controls.Button
            {
                Content = "取消",
                Width = 80,
                Padding = new Thickness(10, 5, 10, 5)
            };
            cancelButton.Click += (s, e) => { DialogResult = false; Close(); };
            buttonPanel.Children.Add(cancelButton);

            grid.Children.Add(buttonPanel);
            Content = grid;
        }
    }
}
