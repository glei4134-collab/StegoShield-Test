using System;
using System.Threading.Tasks;

namespace StegoShield.DirectRegister
{
    class Program
    {
        static async Task Main(string[] args)
        {
            Console.WriteLine("=== StegoShield 直接注册工具 ===\n");

            try
            {
                Console.WriteLine("正在获取用户服务实例...");
                var userService = Services.UserService.Instance;
                Console.WriteLine("✓ 服务已初始化");

                Console.WriteLine("\n开始注册账户...");
                Console.WriteLine("用户名: gongle");
                Console.WriteLine("邮箱: gongle@example.com");
                Console.WriteLine("密码: 685685\n");

                var result = await userService.RegisterAsync("gongle", "gongle@example.com", "685685");

                Console.WriteLine($"\n注册结果: {(result.Success ? "✓ 成功" : "✗ 失败")}");
                Console.WriteLine($"消息: {result.Message}");

                if (result.Success)
                {
                    Console.WriteLine("\n=== 账户注册成功！===");
                    Console.WriteLine("现在你可以使用以下信息登录：");
                    Console.WriteLine("用户名: gongle");
                    Console.WriteLine("密码: 685685");

                    Console.WriteLine("\n正在测试登录功能...");
                    var loginResult = await userService.LoginAsync("gongle", "685685");
                    Console.WriteLine($"登录结果: {(loginResult.Success ? "✓ 成功" : "✗ 失败")}");
                    Console.WriteLine($"消息: {loginResult.Message}");
                }
                else
                {
                    Console.WriteLine($"\n✗ 注册失败: {result.Message}");
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"\n✗ 错误: {ex.Message}");
                Console.WriteLine($"详细错误: {ex}");
            }

            Console.WriteLine("\n按任意键退出...");
            Console.ReadKey();
        }
    }
}
