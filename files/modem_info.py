# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2025 zzzz0317

import json
import subprocess

def get_modem_info():
    try:
        result_proc = subprocess.run(
            ['/usr/libexec/rpcd/modem_ctrl', 'call', 'info'],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result_proc.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None
        
    target_keys = {
        'revision', 'temperature', 'voltage', 'connect_status',
        'SIM Status', 'sim_status', 'ISP', 'CQI UL', 'CQI DL', 'AMBR UL', 'AMBR DL', 'network_mode',
        "MCC", "MNC"
    }
    
    res_data = {}
    result_progress = {}
    result_txt = []
    
    info_list = data.get("info", [])
    if not isinstance(info_list, list) or len(info_list) == 0:
        return None
    
    modem_info = info_list[0].get("modem_info", [])
    if not isinstance(modem_info, list) or len(modem_info) == 0:
        return None
    
    for d in modem_info:
        key = d.get("key")
        if key in target_keys:
            res_data[key] = str(d.get("value", "")).strip()
        
        if d.get("type") == "progress_bar" and d.get("class") == "Cell Information":
            result_progress[str(key).replace(" ", "")] = {
                "value": str(d.get("value", "0")),
                "min_value": str(d.get("min_value", "0")),
                "max_value": str(d.get("max_value", "0")),
                "unit": str(d.get("unit", "")),
            }
    
    default_unknown = "-"
    sim_status = res_data.get('SIM Status', res_data.get('sim_status', 'unknown'))
    if sim_status in ["miss"]:
        default_unknown = "无SIM卡"

    # --- 修复后的 ISP 识别逻辑 ---
    raw_isp = res_data.get("ISP", "")
    # 如果 ISP 是数字、问号或者是空的，则尝试识别
    if raw_isp.isdigit() or raw_isp in ["????", ""] or not raw_isp:
        # 优先用 ISP 里的数字，如果没有则用 MCC+MNC 拼接
        mcc_mnc = raw_isp if raw_isp.isdigit() else f"{res_data.get('MCC', '')}{res_data.get('MNC', '')}"
        
        isp_map = {
            "46000": "中国移动", "46002": "中国移动", "46007": "中国移动", "46008": "中国移动",
            "46001": "中国联通", "46006": "中国联通", "46009": "中国联通",
            "46003": "中国电信", "46005": "中国电信", "46011": "中国电信",
            "46015": "中国广电",
            "46020": "中国铁通"
        }
        res_data["ISP"] = isp_map.get(mcc_mnc, mcc_mnc if mcc_mnc else default_unknown)
    # ---------------------------

    if res_data.get("network_mode", "").endswith(" Mode"):
        res_data["network_mode"] = res_data["network_mode"][:-5]
        
    # CQI / AMBR 格式化
    dl_cqi = res_data.get('CQI DL', '-')
    ul_cqi = res_data.get('CQI UL', '-')
    res_data['CQI'] = f"DL {dl_cqi} UL {ul_cqi}" if dl_cqi != "-" or ul_cqi != "-" else default_unknown
    
    dl_ambr = res_data.get('AMBR DL', '-')
    ul_ambr = res_data.get('AMBR UL', '-')
    res_data['AMBR'] = f"{dl_ambr}/{ul_ambr}" if dl_ambr != "-" or ul_ambr != "-" else default_unknown
    
    # 组装输出文本
    result_txt.append(f"revision:{res_data.get('revision', 'unknown')}")
    result_txt.append(f"temperature:{res_data.get('temperature', 'unknown')}")
    result_txt.append(f"voltage:{res_data.get('voltage', 'unknown')}")
    result_txt.append(f"connect:{res_data.get('connect_status', default_unknown)}")
    result_txt.append(f"sim:{sim_status}")
    result_txt.append(f"isp:{res_data.get('ISP', default_unknown)}")
    result_txt.append(f"cqi:{res_data['CQI']}")
    result_txt.append(f"ambr:{res_data['AMBR']}")
    result_txt.append(f"networkmode:{res_data.get('network_mode', default_unknown)}")
    
    # 信号进度条处理
    prog_keys = list(result_progress.keys())
    for i in range(3):
        if prog_keys:
            pk = prog_keys.pop(0)
            item = result_progress[pk]
            result_txt.append(f"signal{i}name:{pk}")
            result_txt.append(f"signal{i}value:{item['value']}")
            result_txt.append(f"signal{i}min:{item['min_value']}")
            result_txt.append(f"signal{i}max:{item['max_value']}")
            result_txt.append(f"signal{i}unit:{item['value']}/{item['max_value']}{item['unit']}")
        else:
            result_txt.append(f"signal{i}name:-")
            result_txt.append(f"signal{i}value:0")
            result_txt.append(f"signal{i}min:0")
            result_txt.append(f"signal{i}max:0")
            result_txt.append(f"signal{i}unit:-")
    
    return "\n".join(result_txt)

if __name__ == '__main__':
    info = get_modem_info()
    if info:
        print(info)
