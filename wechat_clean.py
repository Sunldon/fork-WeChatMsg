#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import argparse
import sys
import os
from typing import List, Tuple

def read_and_clean_wechat_csv(file_path: str) -> pd.DataFrame:
    """
    读取微信聊天记录CSV文件并进行清理
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        清理后的DataFrame
    """
    try:
        # 读取CSV文件
        df = pd.read_csv(file_path)
        
        # 检查必要的列是否存在
        required_columns = ['IsSender', 'StrContent']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"CSV文件缺少必要的列: {missing_columns}")
        
        # 过滤包含<img和<emoji的消息
        df_filtered = df[~df['StrContent'].astype(str).str.contains(r'<img|<emoji|<voicemsg|voipmsg|videomsg|msg>|<msg', na=False)]
        
        # 去重处理 - 基于IsSender和StrContent去重
        df_clean = df_filtered.drop_duplicates(subset=['IsSender', 'StrContent'])
        
        # 转换IsSender字段：1->other, 其他->self
        df_clean['sender_label'] = df_clean['IsSender'].apply(
            lambda x: 'self' if x == 1 else 'other'
        )
        
        return df_clean
        
    except FileNotFoundError:
        raise FileNotFoundError(f"文件不存在: {file_path}")
    except pd.errors.EmptyDataError:
        raise ValueError("CSV文件为空")
    except Exception as e:
        raise RuntimeError(f"读取CSV文件时出错: {str(e)}")

def generate_markdown_content(df: pd.DataFrame) -> str:
    """
    生成Markdown格式的聊天记录
    
    Args:
        df: 清理后的DataFrame
        
    Returns:
        Markdown格式的字符串
    """
    markdown_lines = [""]
    
    for _, row in df.iterrows():
        sender = row['sender_label']
        content = str(row['StrContent']).strip()
        
        # 处理空内容
        if not content or content == 'nan':
            continue
            
        # 格式化输出：sender: content
        markdown_lines.append(f"{sender}: {content}")
        markdown_lines.append("")

    
    return "\n".join(markdown_lines)

def save_markdown_file(content: str, output_path: str = "wechat_cleaned.md"):
    """
    保存Markdown内容到文件
    
    Args:
        content: Markdown内容
        output_path: 输出文件路径
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"清理后的聊天记录已保存到: {os.path.abspath(output_path)}")
    except Exception as e:
        raise RuntimeError(f"保存文件时出错: {str(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='微信聊天记录CSV文件清理工具')
    parser.add_argument('file_path', help='CSV文件路径')
    parser.add_argument('-o', '--output', default='wechat_cleaned.md', 
                       help='输出Markdown文件路径 (默认: wechat_cleaned.md)')
                       
    
    args = parser.parse_args()
    
    try:
        # 读取并清理数据
        print(f"正在读取文件: {args.file_path}")
        df_clean = read_and_clean_wechat_csv(args.file_path)
        
        # 显示统计信息
        df_original = pd.read_csv(args.file_path)
        original_count = len(df_original)
        
        # 计算过滤掉的消息数量
        filtered_count = len(df_original[df_original['StrContent'].astype(str).str.contains(r'<img|<emoji', na=False)])
        cleaned_count = len(df_clean)
        
        print(f"原始记录数: {original_count}")
        print(f"过滤掉包含<img/<emoji的消息数: {filtered_count}")
        print(f"去重后记录数: {cleaned_count}")
        print(f"总过滤比例: {((original_count - cleaned_count) / original_count * 100):.1f}%")
        
        # 生成Markdown内容
        markdown_content = generate_markdown_content(df_clean)
        
        # 保存文件
        save_markdown_file(markdown_content, args.output)
        
        # 显示预览
        print("\n前5条清理后的记录预览:")
        print("-" * 50)
        preview_lines = markdown_content.split('\n')[:10]
        for line in preview_lines:
            print(line)
        
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()