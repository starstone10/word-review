import streamlit as st
import json
import os
from datetime import datetime, timedelta
import io
from gtts import gTTS

# ================= 配置与初始化 =================
DATA_FILE = "korean_vocab.json"


# 默认数据结构
DEFAULT_DATA = {
    "words": {}, 
    # 结构: { "word": { "meaning": "...", "note": "", "next_review": "2024-01-01", "interval": 0} }
    "streak": 0,          
    "last_login": None,   
    "today_reviewed": [],
    "had_reviewed":0,
    "totalstreak":0,
    "first_day":None
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_DATA.copy()

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= 核心算法 (艾宾浩斯简化版) =================
def calculate_next_review(word_data,ease):
    """根据回答情况计算下次复习时间和间隔"""
    now = datetime.now()
    plan=[0,1,2,4,15,30]
    interval = word_data.get("interval",0)

    if ease<0.5:
        if interval!=len(plan)-1:
            interval=interval+1
        else:
            data["had_review"]+=1
            save_data(data)
            return False
    else:
        interval=max(0,interval-int(ease/0.5))
        

    next_date = now + timedelta(days=plan[interval])
    
    return {
        "next_review": next_date.strftime("%Y-%m-%d"),
        "interval": interval
    }

#音频生成
def get_audio(word):
    audio_dir = "audio"
    os.makedirs(audio_dir, exist_ok=True)
    file_path = os.path.join(audio_dir, f"{word}.mp3")
    if not os.path.exists(file_path):
        tts = gTTS(word, lang='ko')
        tts.save(file_path)

def congratulation(first_day,today,streak):
    fday=first_day[-2:]
    fmonth=first_day[5:7]
    fyear=first_day[:4]

    day=x.strftime("%d")
    month=x.strftime("%m")
    year=x.strftime("%Y")

    if fmonth==x.strftime("%m"):
        if fday==day:
            return "year"
        elif fmonth=="02" and fday=="29" and (x+timedelta(days=1)).strptime("%m")=="03":
            return "year"
    elif fday==day or (fday=="31" and (x+timedelta(days=1)).strptime("%d")=="01") or ((fday=="30" or fday=="29") and month=="02" and (x+timedelta(days=1)).strptime("%d")=="01"):
        return "month"
    
    if streak in [3,7,10,50,100,500,1000]:
            return streak
    else:
            return False

# ================= 页面主逻辑 =================
st.set_page_config(page_title="한국어 단어 암기", page_icon="🇰🇷",initial_sidebar_state="collapsed" )
#st.title("🇰🇷 한국어 단어 암기 (韩语背词)")

data = load_data()
        
# 1. 签到逻辑
x=datetime.now()
today_str = x.strftime("%Y-%m-%d")
if data["last_login"] != today_str:
    data["totalstreak"]+=1
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    data["today_reviewed"]=[]
    if data["last_login"] == yesterday:
        data["streak"] += 1
        cong=congratulation(data["first_day"],x,data["streak"])

    else:
        data["streak"] = 1 # 断签重置
        data["first_day"]=today_str
    data["last_login"] = today_str
    save_data(data)
    

# 侧边栏：上传功能
if "in_review_mode" not in st.session_state:
    st.sidebar.header("📂 단어장 가져오기 (导入词书)")
    uploaded_file = st.sidebar.file_uploader("TXT 파일 업로드(上传TXT文件)", type=["txt"], help="형식: 홀수 줄은 단어, 짝수 줄은 뜻（格式：奇数行是单词，偶数行是释义）")

    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            
            new_count = 0
            for i in range(0, len(lines), 2):
                if i + 1 < len(lines):
                    word = lines[i].strip()
                    meaning = lines[i+1].strip()
                    if word not in data["words"]:
                        data["words"][word] = {
                            "meaning": [meaning],
                            "note": "",
                            "next_review": today_str, # 新词今天就要背
                            "interval": 0
                        }
                        new_count += 1
                        get_audio(word)
                    else:
                        newmeaning=True
                        for j in data["words"][word]["meaning"]:
                            if meaning==j:
                                newmeaning=False
                        if newmeaning:
                            data["words"][word]["meaning"].append(meaning)
                            data["words"][word]["next_review"]=today_str# 新词今天就要背
                            data["words"][word]["interval"]=0
            
            save_data(data)
            st.sidebar.success(f"성공! {new_count}개의 단어를 추가했습니다.（成功！添加了{new_count}个单词。）")
            
        except Exception as e:
            st.sidebar.error(f"불러오기 실패: {str(e)}")


# ================= 状态管理 =================
# 使用 session_state 记录当前是在主页还是复习页
if "in_review_mode" not in st.session_state:
    st.session_state.in_review_mode = False

# ================= 页面 1：主页 (Dashboard) =================
# 获取今日待复习列表
due_words = []
for w, info in data["words"].items():
    if info["next_review"] <= today_str and w not in data.get("today_reviewed", []):
        due_words.append(w)
        
if not st.session_state.in_review_mode:
    st.title("🇰🇷 한국어 단어 암기 (韩语背词)")
    
    # 上半部分：数据展示
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🔥 연속 학습 일수 (连续签到)", value=f"{data['streak']}일")
        st.metric(label="누적 학습 일수 (累计签到)", value=f"{data['totalstreak']}일")
    with col2:
        reviewed_today = len(data.get("today_reviewed", []))
        st.metric(label="✅ 오늘 복습 완료 (今日复习单词)", value=f"{reviewed_today}개")
        had_reviewed = data.get("had_reviewed", 0)
        st.metric(label="공복습 완료 (共复习完毕)", value=f"{had_reviewed}개")
    
    try:
        if cong:
            st.divider()
            if cong=="year":
                st.success("1년 버텼어!맛있는 거 먹고 자기한테 보상해!.（坚持了一年！吃顿好的奖励一下自己吧！）")
            elif cong=="month":
                st.success("한 달 버텼어!맛있는 거 먹고 자기한테 보상해!.（坚持了一个月！吃顿好的奖励一下自己吧！）")
            else:
                st.success(f"단어 외우기 {data['streak']} 일째입니다!.（今天是坚持背单词的第{data['streak']}天！吃顿好的奖励一下自己吧！）")

            if st.button("네, 알겠습니다 (我知道了)"):
                cong=False
                st.rerun()
    except NameError:
        pass
        
    st.divider()
    
    # 下半部分：复习入口按钮
    if due_words:
        reviewbutton=st.empty()
        reviewbutton.markdown(f"### 📝 오늘 복습할 단어(今日要复习的单词): **{len(due_words)}개**")
        if st.button("🚀 시작 (开始复习)", use_container_width=True, type="primary"):
            st.session_state.in_review_mode = True
            st.session_state.review_queue = due_words[:]
            st.session_state.queue = due_words[:]
            st.session_state.writequeue = due_words[:]
            st.session_state.current_word = None
            st.session_state.show_answer = False
            st.session_state.review=False
            st.session_state.totalword=len(due_words)
            st.session_state.easequeue={i:0 for i in st.session_state.review_queue}
            st.session_state.renew=False
            st.rerun()
    else:
        st.success("🎉 오늘의 복습을 모두 마쳤습니다! (今日复习已完成！)")

# ================= 页面 2：复习页 (Review) =================
else:
    st.markdown("""
    <style>
        button[data-key="⬅️ 홈으로 (返回首页)"] {
            margin-top: -20px;
        }
        hr {
            margin-top: -10px;
            margin-bottom: 0px;
        }
    </style>
    """, unsafe_allow_html=True)

    # 顶部返回按钮
    if st.button("⬅️ 홈으로 (返回首页)"):
        st.session_state.in_review_mode = False
        st.rerun()

        
    # 开始复习流程
    if due_words:
        # 使用 Session State 管理当前复习状态
        if 'review_queue' not in st.session_state:
            st.session_state.review_queue = due_words[:]
            st.session_state.queue = due_words[:]
            st.session_state.writequeue = due_words[:]
            st.session_state.current_word = None
            st.session_state.show_answer = False
            st.session_state.review=False
            st.session_state.totalword=len(due_words)
            st.session_state.easequeue={i:0 for i in st.session_state.review_queue}
            st.session_state.renew=False
            
            #st.session_state.spelling_mode = False
            #st.session_state.wrong_spelling_list = [] # 拼写错误的词放这里重练

        queue = st.session_state.queue
        writequeue=st.session_state.writequeue
        st.divider()
        st.subheader("복습(复习)")

        
        if queue:
            current_word = queue[0]
            word_info = data["words"][current_word]

            if st.session_state.show_answer and queue[-1]==queue[0] and len(queue)!=1:
                st.markdown(f"<p style='font-size: 1rem;color=#2e86c1;'>{st.session_state.totalword-len(queue)+2}/{st.session_state.totalword}</p>", unsafe_allow_html=True)
            else:
                st.markdown(f"<p style='font-size: 1rem;color=#2e86c1;'>{st.session_state.totalword-len(queue)+1}/{st.session_state.totalword}</p>", unsafe_allow_html=True)
            # --- 阶段 1: 认读 (是否认识) ---
            if not st.session_state.show_answer:
                placeholder = st.empty()
                with placeholder.container():
                    st.markdown(f"<p style='text-align:center; font-size: 3rem;font-weight: bold;'>{current_word}</p>", unsafe_allow_html=True)
   
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ 알아요 (认识)", use_container_width=True):
                            # 认识 -> 显示释义，进入拼写准备
                            st.session_state.show_answer = True
                            #st.rerun()
                    with c2:
                        if st.button("❌ 몰라요 (不认识)", use_container_width=True):
                            # 不认识 -> 直接算错，更新数据，移到队尾
                            st.session_state.easequeue[current_word]+=0.4
                            # 移动位置：加到最后一个
                            if len(queue)==1 or queue[-1]!=current_word:
                                queue.append(current_word)
                            st.session_state.show_answer = True
                            #st.rerun()
                if st.session_state.show_answer:
                    placeholder.empty()
            
            # --- 阶段 2: 查看释义 & 笔记 ---
            if st.session_state.show_answer:
                    st.markdown(f"<p style='text-align:center; font-size: 3rem;color: #555;font-weight: bold;'>{current_word}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center; font-size: 2.5rem;color: #2e86c1;'>{';'.join(word_info['meaning'])}</p>", unsafe_allow_html=True)

                    st.audio(f"audio/{current_word}.mp3", format='audio/mp3')
                    
                    # 编辑笔记
                    new_note = st.text_area("노트 편집 (编辑笔记)", value=word_info.get("note", ""), key=f"note_{current_word}")
                    if new_note != word_info.get("note", ""):
                        data["words"][current_word]["note"] = new_note
                        save_data(data)

                    if queue[-1]!=current_word or len(queue)==1:
                        c1,c2=st.columns(2)
                        with c1:
                            if st.button("❌ 잘못 기억하다 (记错了)", use_container_width=True):
                                st.session_state.show_answer = False
                                queue.pop(0)
                                queue.append(current_word)
                                st.session_state.easequeue[current_word]+=0.4
                                st.rerun()
                                
                        with c2:
                            if st.button("➡️ 다음(下一个)", use_container_width=True, type="primary"):
                                st.session_state.show_answer = False
                                queue.pop(0)
                                st.rerun()

                    else:
                        if st.button("➡️ 다음(下一个)", use_container_width=True, type="primary"):
                                st.session_state.show_answer = False
                                queue.pop(0)
                                st.rerun()

                    
                        
                        

            # --- 阶段 3: 拼写练习 ---
        if not queue and writequeue:
                current_word = writequeue[0]
                word_info = data["words"][current_word]
                st.markdown(f"<p style='font-size: 1rem;color=#2e86c1;'>{st.session_state.totalword-len(writequeue)+1}/{st.session_state.totalword}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align:center; font-size: 2.5rem;color: #555;font-weight: bold;'>{'；'.join(word_info['meaning'])}</p>",unsafe_allow_html=True)

                if not st.session_state.review:
                    with st.form(key=current_word, clear_on_submit=True):
                        user_input = st.text_input("단어를 입력하세요 (请输入单词)：", key=f"input_{current_word}")
                        submitted = st.form_submit_button("제출 (提交)", use_container_width=True)

                    if submitted:
                        if user_input.strip() == current_word.strip():
                            # 正确逻辑
                            writequeue.pop(0)
                            if st.session_state.renew:#上次拼写错误
                                writequeue.append(current_word)
                                st.session_state.renew=False
                            else:
                                update = calculate_next_review(word_info, st.session_state.easequeue[current_word])
                                if update:
                                    data["words"][current_word].update(update)
                                    data.setdefault("today_reviewed", []).append(current_word)
                                else:
                                    data["words"].pop(current_word)
                                save_data(data)
                            # 完成该词，移出队列
                            save_data(data)
                            st.success("정답입니다! (正确!)")
                            st.balloons()
                            # 延迟一点跳转体验更好，但在streamlit里直接rerun最快
                            st.rerun()
                        else:
                            st.session_state.review=True#显示单词
                            st.session_state.easequeue[current_word]+=0.4
                            st.rerun()

                    st.columns([1,3,1])[1].image("keyboard.jpg")
                    
                else:
                    st.markdown(f"<p style='text-align:center; font-size:4rem; color: #2e86c1;font-weight:bold;'>{current_word}</p>", unsafe_allow_html=True)
                    if st.button(f"다시 맞춤법（重新拼写）", use_container_width=True):
                        st.session_state.review=False
                        st.session_state.renew=True
                        st.rerun()
                        
                
                if st.button("⬅️ 스펠링 건너뛰기 (跳过拼写)"):
                    for i in writequeue:
                        update = calculate_next_review(word_info, st.session_state.easequeue[i]+0.4)
                        if update:
                            data["words"][i].update(update)
                            data.setdefault("today_reviewed", []).append(i)
                        else:
                            data["words"].pop(i)
                        save_data(data)
                    st.session_state.writequeue=[]
                    writequeue=[]
                    st.rerun()
        else:
            # 队列空了
            st.success("오늘 복습할 단어가 없어요.（今天没有要复习的单词了。）")
            if st.button("홈으로 돌아가기 (返回首页)"):
                # 清理 session state
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.session_state.in_review_mode = False
                st.rerun()

    else:
        st.info("🎉 오늘의 복습을 모두 마쳤습니다! (今日复习已完成！)")
