using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using StegoShield.Desktop.Services;

namespace StegoShield.Desktop.Views
{
    public partial class MainWindow : Window
    {
        private UserControl? _currentPage;
        private string _currentPageName = "Encode";

        public MainWindow()
        {
            InitializeComponent();
            UpdateUserInfo();
            try
            {
                LoadPage("Encode");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"加载页面失败: {ex.Message}\n{ex.StackTrace}", "错误", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void TitleBar_MouseLeftButtonDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            if (e.ClickCount == 2)
            {
                WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized;
            }
            else
            {
                DragMove();
            }
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }

        private void UpdateUserInfo()
        {
            var user = UserService.Instance.CurrentUser;
            if (user != null)
            {
                txtUserInfo.Text = $"用户: {user.Username}";
                btnLogout.Content = "登出";
            }
            else
            {
                txtUserInfo.Text = "未登录";
                btnLogout.Content = "登录";
            }
        }

        private void LoadPage(string pageName)
        {
            _currentPageName = pageName;
            MainContentArea.Children.Clear();

            switch (pageName)
            {
                case "Encode":
                    _currentPage = new EncodePage();
                    break;
                case "Decode":
                    _currentPage = new DecodePage();
                    break;
                case "Settings":
                    _currentPage = new SettingsPage();
                    break;
                case "Vip":
                    _currentPage = new VipPage();
                    break;
            }

            if (_currentPage != null)
            {
                MainContentArea.Children.Add(_currentPage);
            }

            UpdateNavButtons();
        }

        private void UpdateNavButtons()
        {
            btnEncode.Style = _currentPageName == "Encode" 
                ? (Style)FindResource("NavButtonSelectedStyle")
                : (Style)FindResource("NavButtonStyle");

            btnDecode.Style = _currentPageName == "Decode"
                ? (Style)FindResource("NavButtonSelectedStyle")
                : (Style)FindResource("NavButtonStyle");

            btnSettings.Style = _currentPageName == "Settings"
                ? (Style)FindResource("NavButtonSelectedStyle")
                : (Style)FindResource("NavButtonStyle");

            btnVip.Style = _currentPageName == "Vip"
                ? (Style)FindResource("NavButtonSelectedStyle")
                : (Style)FindResource("NavButtonStyle");
        }

        private void BtnEncode_Click(object sender, RoutedEventArgs e)
        {
            LoadPage("Encode");
        }

        private void BtnDecode_Click(object sender, RoutedEventArgs e)
        {
            LoadPage("Decode");
        }

        private void BtnSettings_Click(object sender, RoutedEventArgs e)
        {
            LoadPage("Settings");
        }

        private void BtnVip_Click(object sender, RoutedEventArgs e)
        {
            LoadPage("Vip");
        }

        private void BtnLogout_Click(object sender, RoutedEventArgs e)
        {
            if (UserService.Instance.IsLoggedIn)
            {
                var result = MessageBox.Show(
                    "确定要退出登录吗？",
                    "确认",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Question);

                if (result == MessageBoxResult.Yes)
                {
                    UserService.Instance.Logout();
                    var loginWindow = new LoginWindow();
                    loginWindow.Show();
                    this.Close();
                }
            }
            else
            {
                var loginWindow = new LoginWindow();
                loginWindow.Show();
                this.Close();
            }
        }
    }
}
