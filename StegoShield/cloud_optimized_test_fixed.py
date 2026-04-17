"""
StegoShield 云端优化版测试 (修复版)
=====================================
完整支持所有格式:
- PNG/BMP/TIFF: 使用LSB隐写
- JPEG: 使用DCT隐写
- WebP: 使用LSB隐写

增强特性:
- 稳定的多线程并行
- 真实测试数据
- 实时进度显示
- 自动图表生成

作者: StegoShield Cloud Test Suite
日期: 2026-04-17
"""

import sys
import os
import time
import base64
import io
import json
import random
import string
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from PIL import Image
import numpy as np

try:
    from app.services import enhanced_stego, dct_stego
    from app.payload import prepare_payload, parse_payload
    print("✓ StegoShield 服务已加载")
    print("  - LSB隐写 (PNG/BMP/TIFF/WebP)")
    print("  - DCT隐写 (JPEG)")
except ImportError as e:
    print(f"✗ 无法加载服务: {e}")
    sys.exit(1)


@dataclass
class TestResult:
    """测试结果数据类"""
    format_name: str
    data_size: int
    compression_type: str
    compression_level: int
    data_loss_percent: float
    compression_ratio: float
    embed_time_ms: float
    compress_time_ms: float
    extract_time_ms: float
    success: bool
    method: str  # 'lsb' or 'dct'


class CloudTestRunner:
    """
    云端测试运行器（修复版）
    
    完整支持所有图片格式和压缩方式
    """
    
    def __init__(self, loss_threshold: float = 20.0, max_workers: int = 16):
        self.loss_threshold = loss_threshold
        self.max_workers = max_workers
        self.results: List[TestResult] = []
        self.lock = threading.Lock()
        
        # 测试配置
        self.formats = ['PNG', 'JPEG', 'BMP', 'TIFF', 'WEBP']
        
        # 数据大小: 10B到200KB
        self.test_sizes = self._generate_test_sizes()
        
        # 压缩配置: 针对不同格式使用不同隐写方法
        # PNG/BMP/TIFF/WebP -> LSB隐写 -> PNG压缩
        # JPEG -> DCT隐写 -> JPEG压缩
        self.compression_configs = [
            # 无损格式 -> LSB -> PNG压缩
            ('PNG', 'PNG', 'lsb', [9, 6, 3]),
            ('BMP', 'PNG', 'lsb', [9, 6, 3]),
            ('TIFF', 'PNG', 'lsb', [9, 6, 3]),
            ('WEBP', 'PNG', 'lsb', [9, 6, 3]),
            
            # JPEG格式 -> DCT -> JPEG压缩
            ('JPEG', 'JPEG', 'dct', [95, 85, 75, 60, 50]),
        ]
        
        print(f"\n{'='*70}")
        print(f"云端优化测试套件 (修复版)")
        print(f"{'='*70}")
        print(f"丢失率阈值: {self.loss_threshold}%")
        print(f"最大工作线程: {self.max_workers}")
        print(f"测试大小数量: {len(self.test_sizes)}")
        print(f"图片格式: {', '.join(self.formats)}")
    
    def _generate_test_sizes(self) -> List[int]:
        """生成测试数据大小列表"""
        sizes = []
        
        # 极小: 字节级
        sizes.extend([10, 50, 100, 200, 500])
        
        # 小: KB级
        sizes.extend([1024, 2*1024, 5*1024, 10*1024])
        
        # 中: 10-100KB
        sizes.extend([20*1024, 50*1024, 100*1024])
        
        # 大: 100-200KB
        sizes.extend([150*1024, 200*1024])
        
        return sorted(list(set(sizes)))
    
    def create_test_image(self, size: Tuple[int, int], format_name: str) -> bytes:
        """创建测试图片"""
        arr = np.random.randint(0, 255, (*size, 3), dtype=np.uint8)
        img = Image.fromarray(arr, 'RGB')
        buf = io.BytesIO()
        
        if format_name == 'JPEG':
            img.save(buf, format='JPEG', quality=95)
        elif format_name == 'WEBP':
            img.save(buf, format='WEBP', quality=100)
        else:
            img.save(buf, format=format_name)
        
        return buf.getvalue()
    
    def generate_test_data(self, size_bytes: int) -> str:
        """生成测试数据"""
        chars = string.ascii_letters + string.digits + ' ' * 10
        return ''.join(random.choices(chars, k=size_bytes))
    
    def embed_data(self, image_bytes: bytes, test_data: str, 
                   format_name: str, method: str) -> Tuple[bytes, float]:
        """嵌入数据（根据格式选择方法）"""
        t0 = time.perf_counter()
        
        payload = prepare_payload('text', {'text': test_data})
        
        try:
            if method == 'dct':
                # DCT隐写用于JPEG
                embedded_bytes = dct_stego.embed_with_length_prefix(
                    image_bytes, 
                    payload, 
                    quality=75
                )
            else:
                # LSB隐写用于其他格式
                embedded_bytes = enhanced_stego.embed_enhanced(
                    image_bytes,
                    secret_bytes=payload
                )
            
            embed_time = (time.perf_counter() - t0) * 1000
            return embedded_bytes, embed_time
            
        except Exception as e:
            print(f"      嵌入失败: {e}")
            raise
    
    def extract_data(self, compressed_bytes: bytes, method: str) -> Tuple[bytes, float]:
        """提取数据"""
        t0 = time.perf_counter()
        
        try:
            if method == 'dct':
                # DCT提取
                extracted_bytes = dct_stego.extract_with_length_prefix(compressed_bytes)
            else:
                # LSB提取
                extracted_bytes = enhanced_stego.extract_enhanced(compressed_bytes)
            
            extract_time = (time.perf_counter() - t0) * 1000
            return extracted_bytes, extract_time
            
        except Exception as e:
            raise
    
    def run_single_test(self, format_name: str, data_size: int,
                       compression_type: str, compression_level: int,
                       method: str) -> TestResult:
        """运行单个测试"""
        image_size = (1024, 1024)
        
        try:
            # 1. 创建测试图片
            img_bytes = self.create_test_image(image_size, format_name)
            
            # 2. 生成测试数据
            test_data = self.generate_test_data(data_size)
            
            # 3. 嵌入数据
            embedded_bytes, embed_time = self.embed_data(
                img_bytes, test_data, format_name, method
            )
            
            # 4. 压缩
            t1 = time.perf_counter()
            img = Image.open(io.BytesIO(embedded_bytes))
            buf = io.BytesIO()
            
            if compression_type == 'PNG':
                img.save(buf, format='PNG', compress_level=compression_level)
            elif compression_type == 'JPEG':
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(buf, format='JPEG', quality=compression_level)
            
            compressed_bytes = buf.getvalue()
            compress_time = (time.perf_counter() - t1) * 1000
            
            compression_ratio = len(compressed_bytes) / len(embedded_bytes) if len(embedded_bytes) > 0 else 1.0
            
            # 5. 提取数据
            extracted_bytes, extract_time = self.extract_data(compressed_bytes, method)
            
            # 6. 解析结果
            try:
                parsed = parse_payload(extracted_bytes)
                if parsed.get('type') == 'text':
                    extracted_text = parsed.get('text', '')
                else:
                    extracted_text = extracted_bytes.decode('utf-8', errors='ignore')
            except:
                extracted_text = extracted_bytes.decode('utf-8', errors='ignore')
            
            # 7. 计算丢失率
            if test_data == extracted_text:
                data_loss = 0.0
            else:
                min_len = min(len(test_data), len(extracted_text))
                matching = sum(1 for i in range(min_len) if test_data[i] == extracted_text[i])
                data_loss = (1 - matching / len(test_data)) * 100 if len(test_data) > 0 else 0
            
            success = data_loss < self.loss_threshold
            
            return TestResult(
                format_name=format_name,
                data_size=data_size,
                compression_type=compression_type,
                compression_level=compression_level,
                data_loss_percent=data_loss,
                compression_ratio=compression_ratio,
                embed_time_ms=embed_time,
                compress_time_ms=compress_time,
                extract_time_ms=extract_time,
                success=success,
                method=method
            )
            
        except Exception as e:
            return TestResult(
                format_name=format_name,
                data_size=data_size,
                compression_type=compression_type,
                compression_level=compression_level,
                data_loss_percent=100.0,
                compression_ratio=0,
                embed_time_ms=0,
                compress_time_ms=0,
                extract_time_ms=0,
                success=False,
                method=method
            )
    
    def run_parallel_tests(self, tasks: List[Tuple], 
                          progress_interval: int = 20) -> List[TestResult]:
        """并行运行测试"""
        results = []
        total = len(tasks)
        completed = 0
        start_time = time.time()
        
        print(f"\n开始测试: {total} 个任务, {self.max_workers} 个线程")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.run_single_test, *task): task 
                for task in tasks
            }
            
            for future in futures:
                try:
                    result = future.result()
                    results.append(result)
                    
                    with self.lock:
                        completed += 1
                        
                        if completed % progress_interval == 0 or completed == total:
                            elapsed = time.time() - start_time
                            rate = completed / elapsed if elapsed > 0 else 0
                            remaining = (total - completed) / rate if rate > 0 else 0
                            
                            success_count = sum(1 for r in results if r.success)
                            avg_loss = sum(r.data_loss_percent for r in results) / len(results) if results else 0
                            
                            print(f"  [{completed:4d}/{total}] {completed/total*100:5.1f}% | "
                                  f"成功: {success_count:4d} ({success_count/len(results)*100:5.1f}%) | "
                                  f"丢失: {avg_loss:5.2f}% | "
                                  f"{rate:6.1f} 测试/秒 | "
                                  f"剩余: {remaining:6.0f}秒")
                
                except Exception as e:
                    print(f"  任务执行失败: {e}")
        
        total_time = time.time() - start_time
        print(f"\n测试完成! 总耗时: {total_time:.2f}秒")
        print(f"平均速度: {len(results)/total_time:.1f} 测试/秒")
        
        return results
    
    def generate_all_charts(self, output_dir: str = 'charts'):
        """生成所有图表"""
        print(f"\n生成图表...")
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            formats = self.formats
            
            # 创建综合仪表盘
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            
            # 1. 各格式平均丢失率
            ax1 = axes[0, 0]
            avg_loss_by_format = {}
            for fmt in formats:
                fmt_results = [r for r in self.results if r.format_name == fmt]
                if fmt_results:
                    avg_loss_by_format[fmt] = sum(r.data_loss_percent for r in fmt_results) / len(fmt_results)
            
            colors = {'PNG': '#2E86AB', 'JPEG': '#E94F37', 'BMP': '#F39237', 
                     'TIFF': '#8B5CF6', 'WEBP': '#10B981'}
            
            bars = ax1.bar(list(avg_loss_by_format.keys()), 
                          list(avg_loss_by_format.values()),
                          color=[colors.get(f, '#888888') for f in avg_loss_by_format.keys()])
            ax1.set_ylabel('平均数据丢失率 (%)')
            ax1.set_title('各格式抗压能力对比')
            ax1.axhline(y=self.loss_threshold, color='red', linestyle='--', label=f'{self.loss_threshold}% 阈值')
            ax1.legend()
            
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.1f}%', ha='center', va='bottom')
            
            # 2. 成功率对比
            ax2 = axes[0, 1]
            success_rates = []
            for fmt in formats:
                fmt_results = [r for r in self.results if r.format_name == fmt]
                if fmt_results:
                    success_rate = sum(1 for r in fmt_results if r.success) / len(fmt_results) * 100
                    success_rates.append(success_rate)
                else:
                    success_rates.append(0)
            
            wedges, texts, autotexts = ax2.pie(
                [r if r > 0 else 0.1 for r in success_rates], 
                labels=formats, 
                autopct='%1.1f%%',
                colors=[colors.get(f, '#888888') for f in formats]
            )
            ax2.set_title('各格式成功率对比')
            
            # 3. 数据丢失趋势
            ax3 = axes[1, 0]
            for fmt in formats:
                fmt_results = [r for r in self.results if r.format_name == fmt]
                if fmt_results:
                    sizes_kb = sorted(set(r.data_size for r in fmt_results))
                    avg_losses = []
                    for size in sizes_kb:
                        size_results = [r for r in fmt_results if r.data_size == size]
                        avg_loss = sum(r.data_loss_percent for r in size_results) / len(size_results)
                        avg_losses.append(avg_loss)
                    
                    ax3.plot([s/1024 for s in sizes_kb], avg_losses, 
                            marker='o', label=fmt, linewidth=2,
                            color=colors.get(fmt, '#888888'))
            
            ax3.set_xlabel('数据大小 (KB)')
            ax3.set_ylabel('数据丢失率 (%)')
            ax3.set_title('数据丢失率随文件大小变化')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
            ax3.axhline(y=self.loss_threshold, color='red', linestyle='--', alpha=0.7)
            
            # 4. 测试摘要
            ax4 = axes[1, 1]
            ax4.axis('off')
            
            success_count = sum(1 for r in self.results if r.success)
            avg_loss = sum(r.data_loss_percent for r in self.results) / len(self.results) if self.results else 0
            avg_ratio = sum(r.compression_ratio for r in self.results) / len(self.results) if self.results else 0
            
            summary_text = f"""
测试摘要
═══════════════════════════════════════

总测试数: {len(self.results)}
成功数: {success_count} ({success_count/len(self.results)*100:.1f}%)
失败数: {len(self.results) - success_count}

平均数据丢失: {avg_loss:.2f}%
平均压缩率: {avg_ratio:.2%}

隐写方法:
  • LSB: PNG, BMP, TIFF, WEBP
  • DCT: JPEG (抗JPEG压缩)

丢失率阈值: {self.loss_threshold}%
            """
            
            ax4.text(0.5, 0.5, summary_text, fontsize=11, fontfamily='monospace',
                    ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3),
                    transform=ax4.transAxes)
            
            plt.tight_layout()
            plt.savefig(f'{output_dir}/cloud_test_results_fixed.png', dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"✓ 图表已保存: {output_dir}/cloud_test_results_fixed.png")
            
        except ImportError:
            print("✗ matplotlib 未安装，跳过图表生成")
    
    def run_full_suite(self):
        """运行完整测试套件"""
        print("\n" + "="*80)
        print("StegoShield 云端优化版测试套件 (修复版)")
        print("="*80)
        
        # 生成测试任务
        tasks = []
        for fmt, comp_type, method, levels in self.compression_configs:
            for data_size in self.test_sizes:
                for level in levels:
                    tasks.append((fmt, data_size, comp_type, level, method))
        
        print(f"\n总测试任务: {len(tasks)}")
        print(f"测试组合:")
        print(f"  • PNG/BMP/TIFF/WebP: LSB隐写 + PNG压缩")
        print(f"  • JPEG: DCT隐写 + JPEG压缩")
        print(f"预计时间: {len(tasks) / (self.max_workers * 50):.0f} 秒")
        
        self.results = self.run_parallel_tests(tasks, progress_interval=20)
        
        self.generate_all_charts()
        
        self._print_summary()
        
        self._save_results()
    
    def _print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*80)
        print("测试结果摘要")
        print("="*80)
        
        success_count = sum(1 for r in self.results if r.success)
        avg_loss = sum(r.data_loss_percent for r in self.results) / len(self.results) if self.results else 0
        
        print(f"\n总体统计:")
        print(f"  总测试数: {len(self.results)}")
        print(f"  成功数: {success_count} ({success_count/len(self.results)*100:.1f}%)")
        print(f"  平均数据丢失: {avg_loss:.2f}%")
        
        print(f"\n按格式统计:")
        for fmt in self.formats:
            fmt_results = [r for r in self.results if r.format_name == fmt]
            if fmt_results:
                fmt_success = sum(1 for r in fmt_results if r.success)
                fmt_loss = sum(r.data_loss_percent for r in fmt_results) / len(fmt_results)
                method = fmt_results[0].method.upper()
                print(f"  {fmt:6s} ({method:3s}): {fmt_success:3d}/{len(fmt_results):3d} 成功 "
                      f"({fmt_success/len(fmt_results)*100:5.1f}%), 丢失 {fmt_loss:5.2f}%")
        
        print(f"\n按压缩类型统计:")
        for comp_type in ['PNG', 'JPEG']:
            comp_results = [r for r in self.results if r.compression_type == comp_type]
            if comp_results:
                comp_success = sum(1 for r in comp_results if r.success)
                comp_loss = sum(r.data_loss_percent for r in comp_results) / len(comp_results)
                print(f"  {comp_type:6s}: {comp_success:3d}/{len(comp_results):3d} 成功 "
                      f"({comp_success/len(comp_results)*100:5.1f}%), 丢失 {comp_loss:5.2f}%")
        
        if avg_loss < 10:
            rating = "⭐⭐⭐⭐⭐ 优秀"
        elif avg_loss < 20:
            rating = "⭐⭐⭐⭐ 良好"
        else:
            rating = "⭐⭐⭐ 一般"
        
        print(f"\n总体评价: {rating}")
    
    def _save_results(self):
        """保存测试结果"""
        output_file = 'cloud_test_results_fixed.json'
        
        results_dict = [
            {
                'format': r.format_name,
                'data_size': r.data_size,
                'compression_type': r.compression_type,
                'compression_level': r.compression_level,
                'data_loss_percent': r.data_loss_percent,
                'compression_ratio': r.compression_ratio,
                'embed_time_ms': r.embed_time_ms,
                'compress_time_ms': r.compress_time_ms,
                'extract_time_ms': r.extract_time_ms,
                'success': r.success,
                'method': r.method
            }
            for r in self.results
        ]
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': len(self.results),
            'success_count': sum(1 for r in self.results if r.success),
            'avg_loss': sum(r.data_loss_percent for r in self.results) / len(self.results),
            'loss_threshold': self.loss_threshold,
            'max_workers': self.max_workers,
            'results': results_dict
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n结果已保存: {output_file}")


def main():
    """主函数"""
    print("="*80)
    print("StegoShield 云端优化版测试套件 (修复版)")
    print("="*80)
    print("\n修复内容:")
    print("✓ JPEG格式使用DCT隐写 (抗JPEG压缩)")
    print("✓ PNG/BMP/TIFF/WebP使用LSB隐写")
    print("✓ 完整支持所有压缩级别")
    print("✓ 实时进度显示")
    
    import multiprocessing
    cpu_count = multiprocessing.cpu_count()
    print(f"\n检测到 CPU 核心: {cpu_count}")
    
    max_workers = min(16, cpu_count)
    
    runner = CloudTestRunner(
        loss_threshold=20.0,
        max_workers=max_workers
    )
    
    runner.run_full_suite()
    
    print("\n" + "="*80)
    print("所有任务完成!")
    print("="*80)


if __name__ == '__main__':
    main()
