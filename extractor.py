import re
from pdfminer.high_level import extract_text

# ==========================
# 字段名
# ==========================
COLUMNS = [
    "Файл","Наименование организации","ИНН","КПП","ОГРН",
    "БИК","Расчетный счет (р/с)",
    "Корреспондентский счет (к/с)"
]

# ==========================
# 锚点：定位“付款信息区域”
# ==========================
ANCHORS = [
    r"Реквизиты", r"Банковские\s+реквизиты",
    r"Реквизиты\s+и\s+подписи", r"Исполнитель", r"Платежные\s+реквизиты"
]

# ==========================
# 正则模板
# ==========================
RE_PAT = {
    "name": r"(?:Исполнитель[:\-\s]*)?((?:ООО|АНО|ФГБОУ|ГБОУ|ГБУ|ФГБУ|ИП|АО|ЧУ|ФГУП|ГАУ|МАУ|муниципальн\w+)[^\n,]+)",
    "inn":  r"ИНН[:\s]*([0-9]{10,12})|ИНН/КПП[:\s]*([0-9]{10,12})",
    "kpp":  r"КПП[:\s]*([a-zA-Z0-9]{9})|ИНН/КПП[:\s]*[0-9]{10,12}/([a-zA-Z0-9]{9})",
    "ogrn": r"(?:ОГРН|ОГРНИП)[:\s]*([0-9]{13})",
    "bik":  r"(?:БИК|BIC)[^\d]*([0-9]{9})",
    "rs":   r"(?:р/с|P/с|л/с|расчетн\w+)[^\d]*([0-9]{20})",
    "ks":   r"(?:к/с|Корр\.?\s*счет)[^\d]*([0-9]{20})"
}

# ==========================
# PDF 读取文本
# ==========================
def read_pdf(path):
    text = extract_text(path) or ""
    text = text.replace("\u00A0"," ").replace("–","-").replace("—","-")
    text = re.sub(r"[ \t]+"," ", text)
    return text

# ==========================
# 查找包含银行信息的文本区域
# ==========================
def find_blocks(text, win=40):
    lines = text.splitlines()
    blocks = []
    for i, line in enumerate(lines):
        for a in ANCHORS:
            if re.search(a, line, flags=re.IGNORECASE):
                blocks.append("\n".join(lines[i:i+win]))
    blocks.append(text)
    return blocks

# ==========================
# 安全提取正则分组
# ==========================
def first_group(match):
    if not match:
        return None
    if match.lastindex:
        for i in range(1, match.lastindex + 1):
            val = match.group(i)
            if val:
                return val.strip()
    return match.group(0).strip()

# ==========================
# 从文本块中提取字段
# ==========================
def extract_from_block(block):
    out = {}
    m = re.search(RE_PAT["name"], block, re.IGNORECASE)
    out["name"] = first_group(m)
    for key in ["inn","kpp","ogrn","bik","rs","ks"]:
        m = re.search(RE_PAT[key], block, re.IGNORECASE)
        out[key] = first_group(m)
    return out

# ==========================
# 评分：用于选择最完整的一段
# ==========================
def score(rec):
    sc = 0
    if rec["name"]: sc += 2
    if rec["inn"] and rec["inn"].isdigit() and len(rec["inn"]) in (10, 12): sc += 2
    if rec["ogrn"] and rec["ogrn"].isdigit() and len(rec["ogrn"]) == 13: sc += 2
    if rec["bik"] and rec["bik"].isdigit() and len(rec["bik"]) == 9: sc += 2
    if rec["rs"] and rec["rs"].isdigit() and len(rec["rs"]) == 20: sc += 2
    if rec["ks"] and rec["ks"].isdigit() and len(rec["ks"]) == 20: sc += 1
    return sc

# ==========================
# 对外接口函数：输入 PDF 文件 → 返回收款人信息
# ==========================
def extract_payment_info(pdf_path):
    text = read_pdf(pdf_path)

    best, best_sc = None, -1
    for blk in find_blocks(text):
        rec = extract_from_block(blk)
        sc = score(rec)
        if sc > best_sc:
            best, best_sc = rec, sc

    return best
