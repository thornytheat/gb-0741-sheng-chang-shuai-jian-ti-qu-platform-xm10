REASONS = {
    'ROW_WIDTH': '记录列数不符', 'BAND_INVALID': '频带中心无效', 'SAMPLE_INVALID': '采样序号无效',
    'AMPLITUDE_MISSING': '振幅缺失', 'AMPLITUDE_INVALID': '振幅格式或范围无效',
    'CAL_INVALID': '采样率、增益或灵敏度无效', 'UNIT_INVALID': '压力或电压单位不受支持',
    'CAL_CONFLICT': '同一频带采样配置不一致', 'DUPLICATE_CONFLICT': '同一采样点数值矛盾',
    'MISSING_POINTS': '记录中间存在缺采样点', 'TRUNCATED_BAND': '记录尾部短于声明长度',
    'EXTRA_POINTS': '采样点超出声明长度', 'ROW_ISOLATED': '该频带存在无效采样行',
    'NO_ENERGY': '有效响应能量为零', 'TAIL_TOO_SHORT': '直达声后没有足够尾段',
    'DYNAMIC_RANGE': '声衰减深度不足', 'WINDOW_TOO_SHORT': '回归区间采样点不足',
    'NON_DECAYING': '回归斜率无效', 'LOW_LINEARITY': '回归线性度低于阈值',
    'T_DISAGREEMENT': 'T20 与 T30 差异超过阈值', 'DUPLICATE_ROW': '同一采样点的相同副本',
}


def reason(code):
    return {'code': code, 'message': REASONS[code]}
