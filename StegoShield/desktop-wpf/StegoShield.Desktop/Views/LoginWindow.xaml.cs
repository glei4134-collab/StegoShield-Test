using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Media.Animation;
using StegoShield.Desktop.Services;

namespace StegoShield.Desktop.Views
{
    public partial class LoginWindow : Window
    {
        private bool _isLoggingIn = false;
        private bool _isRegistering = false;
        private bool _isPasswordVisible = false;
        private bool _isDarkTheme = false;

        private const int GWL_EXSTYLE = -20;
        private const int WS_EX_TOOLWINDOW = 0x00000080;
        private const int WS_EX_NOACTIVATE = 0x08000000;

        [DllImport("user32.dll")]
        private static extern int GetWindowLong(IntPtr hwnd, int index);

        [DllImport("user32.dll")]
        private static extern int SetWindowLong(IntPtr hwnd, int index, int newStyle);

        public LoginWindow()
        {
            InitializeComponent();
            
            // Temporarily disabled for testing
            // this.SourceInitialized += LoginWindow_SourceInitialized;
            // Temporarily disabled for testing
            // LoadUserSettings();
            // Temporarily disabled for testing
            // CheckBackendStatus();
            SetupEventHandlers();
        }

        private void LoginWindow_SourceInitialized(object sender, EventArgs e)
        {
            IntPtr hwnd = new WindowInteropHelper(this).Handle;
            int extendedStyle = GetWindowLong(hwnd, GWL_EXSTYLE);
            SetWindowLong(hwnd, GWL_EXSTYLE, extendedStyle | WS_EX_TOOLWINDOW);
        }

        private void SetupEventHandlers()
        {
            txtUsername.TextChanged += TxtUsername_TextChanged;
            txtPassword.PasswordChanged += TxtPassword_PasswordChanged;
        }

        private void TitleBar_MouseLeftButtonDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            DragMove();
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }

        private void TxtUsername_TextChanged(object sender, System.Windows.Controls.TextChangedEventArgs e)
        {
            lblUsername.Visibility = txtUsername.Text.Length > 0 ? Visibility.Collapsed : Visibility.Visible;
            btnClearUsername.Visibility = txtUsername.Text.Length > 0 ? Visibility.Visible : Visibility.Collapsed;
        }

        private void TxtPassword_PasswordChanged(object sender, RoutedEventArgs e)
        {
            lblPassword.Visibility = txtPassword.Password.Length > 0 ? Visibility.Collapsed : Visibility.Visible;
        }

        private void LoadUserSettings()
        {
            try
            {
                string settingsPath = System.IO.Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "StegoShield",
                    "settings.txt"
                );

                if (File.Exists(settingsPath))
                {
                    string[] lines = File.ReadAllLines(settingsPath);
                    foreach (string line in lines)
                    {
                        if (line.StartsWith("RememberMe=True"))
                        {
                            chkRememberMe.IsChecked = true;
                        }
                        else if (line.StartsWith("Username="))
                        {
                            string username = line.Substring("Username=".Length);
                            if (!string.IsNullOrEmpty(username))
                            {
                                txtUsername.Text = username;
                                lblUsername.Visibility = Visibility.Collapsed;
                            }
                        }
                        else if (line.StartsWith("Password="))
                        {
                            string password = line.Substring("Password=".Length);
                            if (!string.IsNullOrEmpty(password))
                            {
                                txtPassword.Password = password;
                                lblPassword.Visibility = Visibility.Collapsed;
                            }
                        }
                        else if (line.StartsWith("DarkTheme="))
                        {
                            bool isDark = line.Substring("DarkTheme=".Length) == "True";
                            if (isDark)
                            {
                                ToggleDarkTheme();
                            }
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"加载设置失败: {ex.Message}");
            }
        }

        private void SaveUserSettings()
        {
            try
            {
                string appDataPath = System.IO.Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                    "StegoShield"
                );

                if (!Directory.Exists(appDataPath))
                {
                    Directory.CreateDirectory(appDataPath);
                }

                string settingsPath = System.IO.Path.Combine(appDataPath, "settings.txt");
                
                using (StreamWriter writer = new StreamWriter(settingsPath))
                {
                    writer.WriteLine($"RememberMe={chkRememberMe.IsChecked}");
                    writer.WriteLine($"DarkTheme={_isDarkTheme}");
                    
                    if (chkRememberMe.IsChecked == true)
                    {
                        writer.WriteLine($"Username={txtUsername.Text}");
                        writer.WriteLine($"Password={txtPassword.Password}");
                    }
                    else
                    {
                        writer.WriteLine("Username=");
                        writer.WriteLine("Password=");
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"保存设置失败: {ex.Message}");
            }
        }

        private async void CheckBackendStatus()
        {
            txtStatus.Text = "正在连接...";
            UpdateStatusIndicator(Colors.Orange, "正在连接...");

            bool isRunning = await ApiService.Instance.IsBackendRunningAsync();
            
            if (isRunning)
            {
                UpdateStatusIndicator(Color.FromRgb(52, 199, 89), "服务器已就绪");
            }
            else
            {
                UpdateStatusIndicator(Color.FromRgb(255, 59, 48), "服务器未连接");
            }
        }

        private void UpdateStatusIndicator(Color color, string message)
        {
            txtStatus.Text = message;
            statusIndicator.Fill = new SolidColorBrush(color);
            
            if (color == Color.FromRgb(52, 199, 89))
            {
                statusIndicator.Effect = new System.Windows.Media.Effects.DropShadowEffect
                {
                    ShadowDepth = 0,
                    BlurRadius = 6,
                    Opacity = 0.7,
                    Color = Color.FromRgb(52, 199, 89)
                };
            }
            else
            {
                statusIndicator.Effect = null;
            }
        }

        private void BtnClearUsername_Click(object sender, RoutedEventArgs e)
        {
            txtUsername.Text = "";
            txtUsername.Focus();
        }

        private void BtnTogglePassword_Click(object sender, RoutedEventArgs e)
        {
            _isPasswordVisible = !_isPasswordVisible;
            
            if (_isPasswordVisible)
            {
                txtPassword.Visibility = Visibility.Collapsed;
                btnTogglePassword.Content = "🙈";
                btnTogglePassword.ToolTip = "隐藏密码";
            }
            else
            {
                txtPassword.Visibility = Visibility.Visible;
                btnTogglePassword.Content = "👁";
                btnTogglePassword.ToolTip = "显示密码";
            }
        }

        private void ToggleDarkTheme()
        {
            _isDarkTheme = !_isDarkTheme;
            
            if (_isDarkTheme)
            {
                this.Background = new SolidColorBrush(Color.FromRgb(30, 30, 40));
            }
            else
            {
                this.Background = new SolidColorBrush(Color.FromRgb(240, 240, 240));
            }
        }

        private void BtnLogin_Click(object sender, RoutedEventArgs e)
        {
            if (_isLoggingIn) return;

            var username = txtUsername.Text.Trim();
            var password = txtPassword.Password;

            if (string.IsNullOrEmpty(username))
            {
                ShowError("请输入用户名");
                ShakeControl(txtUsername);
                return;
            }

            if (string.IsNullOrEmpty(password))
            {
                ShowError("请输入密码");
                ShakeControl(txtPassword);
                return;
            }

            if (password.Length < 6)
            {
                ShowError("密码至少6位");
                ShakeControl(txtPassword);
                return;
            }

            LoginAsync(username, password);
        }

        private void ShakeControl(UIElement control)
        {
            var transform = new TranslateTransform();
            control.RenderTransform = transform;

            var animation = new DoubleAnimationUsingKeyFrames();
            animation.Duration = TimeSpan.FromMilliseconds(400);

            animation.KeyFrames.Add(new LinearDoubleKeyFrame(0, KeyTime.FromPercent(0)));
            animation.KeyFrames.Add(new LinearDoubleKeyFrame(-5, KeyTime.FromPercent(0.25)));
            animation.KeyFrames.Add(new LinearDoubleKeyFrame(5, KeyTime.FromPercent(0.5)));
            animation.KeyFrames.Add(new LinearDoubleKeyFrame(-5, KeyTime.FromPercent(0.75)));
            animation.KeyFrames.Add(new LinearDoubleKeyFrame(0, KeyTime.FromPercent(1)));

            transform.BeginAnimation(TranslateTransform.XProperty, animation);
        }

        private async void LoginAsync(string username, string password)
        {
            _isLoggingIn = true;
            
            try
            {
                if (btnLogin != null)
                {
                    btnLogin.IsEnabled = false;
                    btnLogin.Content = "登录中...";
                }
                
                UpdateStatusIndicator(Color.FromRgb(0, 122, 255), "正在登录...");

                var (success, message) = await UserService.Instance.LoginAsync(username, password);

                if (success)
                {
                    ShowSuccess("登录成功！");
                    SaveUserSettings();
                    
                    var mainWindow = new MainWindow();
                    mainWindow.Show();
                    this.Close();
                }
                else
                {
                    ShowError(message ?? "未知错误");
                }
            }
            catch (Exception ex)
            {
                ShowError("登录失败: " + (ex.Message ?? ex.GetType().Name));
            }
            finally
            {
                _isLoggingIn = false;
                if (btnLogin != null)
                {
                    btnLogin.IsEnabled = true;
                    btnLogin.Content = "登 录";
                }
            }
        }

        private void BtnRegister_Click(object sender, RoutedEventArgs e)
        {
            var registerWindow = new RegisterWindow();
            registerWindow.Show();
            this.Close();
        }

        private void ShowError(string message)
        {
            if (string.IsNullOrWhiteSpace(message))
            {
                message = "未知错误";
            }
            
            UpdateStatusIndicator(Color.FromRgb(255, 59, 48), message);
        }

        private void ShowSuccess(string message)
        {
            UpdateStatusIndicator(Color.FromRgb(52, 199, 89), message);
        }
    }
}