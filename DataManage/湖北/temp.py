#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
湖北电站节点城市分类工具
功能：读取电站节点数据，自动识别所属地级市，生成Excel文件
作者：Monica AI Assistant
日期：2026-02-25
"""

import pandas as pd
import sys
import os

# 定义城市关键词映射表
city_keywords = {
    '恩施州': ['恩施', '沿神', '天上坪', '齐岳山', '德胜', '万寺坪', '洞坪', '老渡口',
               '板桥', '东升', '元堡', '寒池', '鼓乡', '十字路', '建始', '巴东', '宣恩',
               '咸丰', '来凤', '鹤峰', '利川'],

    '武汉市': ['东湖燃机', '武昌燃机', '阳逻', '黄陂', '沌口', '武钢', '青山热电',
               '汉口', '武昌', '汉阳', '江夏', '蔡甸', '新洲', '东西湖', '洪山',
               '江岸', '江汉', '硚口', '汉南'],

    '孝感市': ['孝感', '孝昌', '孝南', '汉川', '应城', '安陆', '官垱', '童沙', '牌楼',
               '曙丰', '金迪', '金灿', '孚旭', '果园场', '中馆驿', '信百', '昇辉',
               '铁门岗', '高投', '星业', '星朗', '大悟', '云梦'],

    '襄阳市': ['襄阳', '襄樊', '盛源', '华龙', '新襄棉', '崔家营', '老河口', '枣阳',
               '宜城', '南漳', '谷城', '保康', '襄州', '樊城', '襄城'],

    '黄冈市': ['黄冈', '大别山', '芳畈', '窑河', '白莲河', '石佛寺', '蔡家寨', '黄土岗',
               '纯阳山', '阎家河', '天明', '二程', '麻城', '武穴', '红安', '罗田',
               '英山', '浠水', '蕲春', '黄梅', '团风'],

    '黄石市': ['黄石', '鑫光', '西塞', '华泰', '晟唐', '东阳光', '大冶', '阳新',
               '下陆', '铁山', '黄石港'],

    '宜昌市': ['宜昌', '三峡', '葛洲坝', '葛二江', '葛大江', '寺坪', '王甫洲',
               '宜都', '当阳', '枝江', '远安', '兴山', '秭归', '长阳', '五峰',
               '西陵', '伍家岗', '点军', '猇亭', '夷陵'],

    '荆州市': ['荆州', '石首', '监利', '沙市', '南郡', '洪湖', '松滋', '公安',
               '江陵', '荆州区', '沙市区'],

    '荆门市': ['荆门', '罗汉寺', '京山', '楚韵', '沙洋', '钟祥', '东宝', '掇刀'],

    '咸宁市': ['咸宁', '蒲圻', '向阳湖', '汀泗桥', '赤壁', '嘉鱼', '通城', '崇阳',
               '通山', '咸安', '温泉'],

    '十堰市': ['十堰', '京蒿', '丹江', '武当湖', '雅口', '梁堰', '桐柏', '郧阳',
               '郧西', '竹山', '竹溪', '房县', '茅箭', '张湾'],

    '鄂州市': ['鄂州', '华盛', '京能', '华容', '梁子湖', '鄂城'],

    '仙桃市': ['仙桃', '仙东', '东旭', '汉盛', '沔阳'],

    '天门市': ['天门', '华湖', '天顺', '上巴河', '竟陵', '岳口'],

    '潜江市': ['潜江', '周家垸', '三里坪', '园林', '广华', '杨市'],
}


def get_city(node_name):
    """
    根据节点名称识别所属城市

    参数:
        node_name: 节点名称字符串

    返回:
        城市名称，如果无法识别则返回"待确认"
    """
    if pd.isna(node_name):
        return '待确认'

    node_name = str(node_name)

    # 遍历所有城市的关键词
    for city, keywords in city_keywords.items():
        for keyword in keywords:
            if keyword in node_name:
                return city

    return '待确认'


def read_data_file(file_path):
    """
    读取数据文件，支持txt、csv、xlsx格式

    参数:
        file_path: 文件路径

    返回:
        DataFrame对象
    """
    file_ext = os.path.splitext(file_path)[1].lower()

    try:
        if file_ext == '.txt':
            # 读取TXT文件，假设是Tab分隔
            df = pd.read_csv(file_path, sep='\t', header=None, encoding='utf-8')
            if df.shape[1] >= 2:
                df.columns = ['序号', '节点名称'] + [f'列{i}' for i in range(2, df.shape[1])]
            else:
                df.columns = ['节点名称']
                df.insert(0, '序号', range(1, len(df) + 1))

        elif file_ext == '.csv':
            df = pd.read_csv(file_path, encoding='utf-8')
            if '节点名称' not in df.columns and df.shape[1] >= 2:
                df.columns = ['序号', '节点名称'] + list(df.columns[2:])

        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            if '节点名称' not in df.columns and df.shape[1] >= 2:
                df.columns = ['序号', '节点名称'] + list(df.columns[2:])

        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")

        return df

    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        sys.exit(1)


def process_nodes(input_file, output_file=None):
    """
    处理节点数据，添加城市信息

    参数:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选）
    """
    print("=" * 60)
    print("🚀 湖北电站节点城市分类工具")
    print("=" * 60)

    # 读取数据
    print(f"\n📖 正在读取文件: {input_file}")
    df = read_data_file(input_file)
    print(f"✅ 成功读取 {len(df)} 条数据")

    # 识别城市
    print("\n🔍 正在识别城市...")
    df['所属地级市'] = df['节点名称'].apply(get_city)

    # 统计信息
    print(f"\n✅ 处理完成！共处理 {len(df)} 条数据")
    print("\n📊 城市分布统计：")
    print("-" * 40)
    city_stats = df['所属地级市'].value_counts()
    for city, count in city_stats.items():
        print(f"  {city:12s} {count:4d} 条")

    # 检查未识别的节点
    unrecognized = df[df['所属地级市'] == '待确认']
    if len(unrecognized) > 0:
        print(f"\n⚠️  有 {len(unrecognized)} 条数据未能识别城市，已标记为'待确认'")
        print("   请手动核对以下节点：")
        for idx, row in unrecognized.head(5).iterrows():
            print(f"   - {row['节点名称']}")
        if len(unrecognized) > 5:
            print(f"   ... 还有 {len(unrecognized) - 5} 条")

    # 保存结果
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_城市分类结果.xlsx"

    print(f"\n💾 正在保存结果到: {output_file}")
    df.to_excel(output_file, index=False, engine='openpyxl')
    print("✅ 保存成功！")

    print("\n" + "=" * 60)
    print("🎉 全部完成！")
    print("=" * 60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python process_nodes.py <输入文件> [输出文件]")
        print("\n示例:")
        print("  python process_nodes.py data.txt")
        print("  python process_nodes.py data.xlsx output.xlsx")
        print("\n支持的文件格式: .txt, .csv, .xlsx, .xls")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_file):
        print(f"❌ 错误: 文件不存在 - {input_file}")
        sys.exit(1)

    process_nodes(input_file, output_file)


if __name__ == "__main__":
    main()
