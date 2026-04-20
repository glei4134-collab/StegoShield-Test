using System;
using System.Text.RegularExpressions;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Animation;
using StegoShield.Desktop.Services;

namespace StegoShield.Desktop.Views
{
    public partial class RegisterWindow : Window
    {
        private bool _isRegistering = false;
        private bool _isPasswordVisible = false;
        private bool _isConfirmPasswordVisible = false;

        public RegisterWindow()
        {
            InitializeComponent();
            SetupEventHandlers();
        }

        private void SetupEventHandlers()
        {
            txtUsername.TextChanged += TxtUsername_TextChanged;
            txtEmail.TextChanged += TxtEmail_TextChanged;
            txtPassword.PasswordChanged += TxtPassword_PasswordChanged;
            txtConfirmPassword.PasswordChanged += TxtConfirmPassword_PasswordChanged;
        }

        private void TitleBar_MouseLeftButtonDown(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            DragMove();
        }

        private void BtnClose_Click(object sender, RoutedEventArgs e)
        {
            Application.Current.Shutdown();
        }

        private void TxtUsername_TextChanged(object sender, TextChangedEventArgs e)
        {
            lblUsername.Visibility = txtUsername.Text.Length > 0 ? Visibility.Collapsed : Visibility.Visible;
            btnClearUsername.Visibility = txtUsername.Text.Length > 0 ? Visibility.Visible : Visibility.Collapsed;
        }

        private void TxtEmail_TextChanged(object sender, TextChangedEventArgs e)
        {
            lblEmail.Visibility = txtEmail.Text.Length > 0 ? Visibility.Collapsed : Visibility.Visible;
            btnClearEmail.Visibility = txtEmail.Text.Length > 0 ? Visibility.Visible : Visibility.Collapsed;
        }

        private void TxtPassword_PasswordChanged(object sender, RoutedEventArgs e)
        {
            lblPassword.Visibility = txtPassword.Password.Length > 0 ? Visibility.Collapsed : Visibility.Visible;
            UpdatePasswordStrength(txtPassword.Password);
        }

        private void TxtConfirmPassword_PasswordChanged(object sender, RoutedEventArgs e)
        {
            lblConfirmPassword.Visibility = txtConfirmPassword.Password.Length > 0 ? Visibility.Collapsed : Visibility.Visible;
        }

        private void UpdatePasswordStrength(string password)
        {
            if (string.IsNullOrEmpty(password))
            {
                txtPwdStrength.Text = "密码强度：未输入";
                txtPwdStrength.Foreground = new SolidColorBrush(Color.FromRgb(153, 153, 153));
                pwdStrengthBar.Width = 0;
                pwdStrengthBar.Background = new SolidColorBrush(Color.FromRgb(224, 224, 224));
                return;
            }

            int strength = 0;
            
            if (password.Length >= 6) strength++;
            if (password.Length >= 8) strength++;
            if (Regex.IsMatch(password, @"[A-Z]")) strength++;
            if (Regex.IsMatch(password, @"[a-z]")) strength++;
            if (Regex.IsMatch(password, @"[0-9]")) strength++;
            if (Regex.IsMatch(password, @"[!@#$%^&*(),.?"":{}|<>]")) strength++;

            if (strength <= 2)
            {
                txtPwdStrength.Text = "密码强度：弱";
                txtPwdStrength.Foreground = new SolidColorBrush(Color.FromRgb(255, 59, 48));
                pwdStrengthBar.Width = 60;
                pwdStrengthBar.Background = new SolidColorBrush(Color.FromRgb(255, 59, 48));
            }
            else if (strength <= 4)
            {
                txtPwdStrength.Text = "密码强度：中";
                txtPwdStrength.Foreground = new SolidColorBrush(Color.FromRgb(255, 149, 0));
                pwdStrengthBar.Width = 150;
                pwdStrengthBar.Background = new SolidColorBrush(Color.FromRgb(255, 149, 0));
            }
            else
            {
                txtPwdStrength.Text = "密码强度：强";
                txtPwdStrength.Foreground = new SolidColorBrush(Color.FromRgb(52, 199, 89));
                pwdStrengthBar.Width = 220;
                pwdStrengthBar.Background = new SolidColorBrush(Color.FromRgb(52, 199, 89));
            }
        }

        private void BtnClearUsername_Click(object sender, RoutedEventArgs e)
        {
            txtUsername.Text = "";
            txtUsername.Focus();
        }

        private void BtnClearEmail_Click(object sender, RoutedEventArgs e)
        {
            txtEmail.Text = "";
            txtEmail.Focus();
        }

        private void BtnTogglePassword_Click(object sender, RoutedEventArgs e)
        {
            _isPasswordVisible = !_isPasswordVisible;
            
            if (_isPasswordVisible)
            {
                txtPassword.Visibility = Visibility.Collapsed;
                btnTogglePassword.Content = "🙈";
            }
            else
            {
                txtPassword.Visibility = Visibility.Visible;
                btnTogglePassword.Content = "👁";
            }
        }

        private void BtnToggleConfirmPassword_Click(object sender, RoutedEventArgs e)
        {
            _isConfirmPasswordVisible = !_isConfirmPasswordVisible;
            
            if (_isConfirmPasswordVisible)
            {
                txtConfirmPassword.Visibility = Visibility.Collapsed;
                btnToggleConfirmPassword.Content = "🙈";
            }
            else
            {
                txtConfirmPassword.Visibility = Visibility.Visible;
                btnToggleConfirmPassword.Content = "👁";
            }
        }

        private void BtnBack_Click(object sender, RoutedEventArgs e)
        {
            var loginWindow = new LoginWindow();
            loginWindow.Show();
            this.Close();
        }

        private bool ValidateForm()
        {
            string username = txtUsername.Text.Trim();
            string email = txtEmail.Text.Trim();
            string password = txtPassword.Password;
            string confirmPassword = txtConfirmPassword.Password;

            if (string.IsNullOrEmpty(username))
            {
                ShowError("请输入用户名");
                ShakeControl(txtUsername);
                return false;
            }

            if (username.Length < 3 || username.Length > 20)
            {
                ShowError("用户名长度必须在3-20个字符之间");
                ShakeControl(txtUsername);
                return false;
            }

            if (!Regex.IsMatch(username, @"^[a-zA-Z0-9_]+$"))
            {
                ShowError("用户名只能包含字母、数字和下划线");
                ShakeControl(txtUsername);
                return false;
            }

            if (string.IsNullOrEmpty(email))
            {
                ShowError("请输入邮箱地址");
                ShakeControl(txtEmail);
                return false;
            }

            if (!Regex.IsMatch(email, @"^[\w\.-]+@[\w\.-]+\.\w+$"))
            {
                ShowError("请输入有效的邮箱地址");
                ShakeControl(txtEmail);
                return false;
            }

            if (string.IsNullOrEmpty(password))
            {
                ShowError("请输入密码");
                ShakeControl(txtPassword);
                return false;
            }

            if (password.Length < 6)
            {
                ShowError("密码至少需要6位");
                ShakeControl(txtPassword);
                return false;
            }

            if (password != confirmPassword)
            {
                ShowError("两次输入的密码不一致");
                ShakeControl(txtConfirmPassword);
                return false;
            }

            if (chkAgreeTerms.IsChecked != true)
            {
                ShowError("请阅读并同意服务条款和隐私政策");
                return false;
            }

            return true;
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

        private async void BtnRegister_Click(object sender, RoutedEventArgs e)
        {
            if (_isRegistering) return;

            if (!ValidateForm()) return;

            string username = txtUsername.Text.Trim();
            string email = txtEmail.Text.Trim();
            string password = txtPassword.Password;

            _isRegistering = true;
            btnRegister.IsEnabled = false;
            UpdateStatus("正在注册...", Color.FromRgb(0, 122, 255));

            try
            {
                var response = await UserService.Instance.RegisterAsync(username, email, password);

                if (response.Success)
                {
                    UpdateStatus("注册成功！", Color.FromRgb(52, 199, 89));
                    
                    MessageBox.Show(
                        $"恭喜！账号注册成功！\n\n用户名：{username}\n\n正在自动登录...",
                        "注册成功",
                        MessageBoxButton.OK,
                        MessageBoxImage.Information
                    );

                    var loginResult = await UserService.Instance.LoginAsync(username, password);
                    if (loginResult.Success)
                    {
                        var mainWindow = new MainWindow();
                        mainWindow.Show();
                        this.Close();
                    }
                    else
                    {
                        MessageBox.Show(
                            "注册成功，但自动登录失败。请手动登录。",
                            "提示",
                            MessageBoxButton.OK,
                            MessageBoxImage.Warning
                        );
                        var loginWindow = new LoginWindow();
                        loginWindow.Show();
                        this.Close();
                    }
                }
                else
                {
                    ShowError(response.Message);
                }
            }
            catch (Exception ex)
            {
                ShowError("注册失败：" + ex.Message);
            }
            finally
            {
                _isRegistering = false;
                btnRegister.IsEnabled = true;
            }
        }

        private void UpdateStatus(string message, Color color)
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

        private void ShowError(string message)
        {
            UpdateStatus(message, Color.FromRgb(255, 59, 48));
        }
    }
}