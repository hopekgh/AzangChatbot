import os
import streamlit as st
from llm.base import llm_list
from utils.messages import language_list, Messages_translator
from utils.streamlit import *

def Setting():
    st.set_page_config(
        page_title="aIkNow Healthcare"
    )
    Setting_session_state()
    Setting_language()
    global main_path, faiss_path
    main_path = os.getcwd()
    faiss_path = os.path.join(main_path, "ForFAISS")
    if not os.path.isdir(faiss_path):
        os.mkdir(faiss_path)

def Sidebar():
    global chat_model
    with st.sidebar:
        # 언어 설정
        user_language = st.selectbox(
            label= "LANGUAGE",
            options= language_list,
            index= 21,
            key="user_language",
            on_change=Cache_language_status
        )

        # ai 모델 설정
        chosen_llm = st.selectbox(
            label=st.session_state.system_messages["choice"] + " llm!",
            options=llm_list,
        )
        api_token = st.text_input(label=st.session_state.system_messages["write"]+" huggingface api token!", placeholder="HUGGINGFACEHUB_API_KEY", type="password")
        chat_model = None
        load_model = st.button(
            label=st.session_state.system_messages["model"]["request"],
            use_container_width=True,
            )
        if chosen_llm == "None" or not api_token:
            st.session_state.model_prepare = False
        if load_model and chosen_llm != "None" and api_token:
            st.session_state.model_prepare = True
        if st.session_state.model_prepare == True and chosen_llm != "None" and api_token:
            chat_model = Load_chat_model(chosen_llm, api_token)
            if chat_model:
                st.write("LLM "+st.session_state.system_messages["complete"])
        
        # RAG를 위한 데이터베이스 생성.
        # 1회 설정 후에는 재설정하지 않아도 괜찮도록 구현
        if st.session_state.RAG_prepare == False:
            rag_prepare = st.button(
                label=st.session_state.system_messages["RAG"]["request"],
                use_container_width= True
            )
            if rag_prepare:
                if not os.path.isfile(os.path.join(faiss_path, "index.faiss")):
                    Prepare_for_RAG(main_path, faiss_path)
                st.session_state.RAG_prepare = True
                st.rerun()
        if st.session_state.RAG_prepare == True:
            st.write("RAG "+st.session_state.system_messages["complete"])

def main():
    st.title(st.session_state.system_messages["title"])
    
    # 대화 로그 출력
    if st.session_state.memory:
        for item in st.session_state.memory:
            st.chat_message(name=item["role"]).write(item["content"])

    # ai가 생성한 영어를 유저 언어로 번역하는 인스턴스 호출
    eng_2_ulang = Messages_translator(st.session_state.user_language, to_eng= False)

    # phase 1: progress = start
    # 유저한테서 기본적인 정보 받아옴
    if st.session_state.progress == "start":
        with st.chat_message("assistant"):
            st.write(st.session_state.ai_messages["intro"])
        if st.session_state.user_input_instance:
            st.error(st.session_state.system_messages["send_to_ai"]["error"])
            st.session_state.user_input_instance = ""
        form_item_list = list(Format_form.form_choices_dict.keys())
        with st.expander(label=st.session_state.system_messages["poop_info_request"], expanded=True):
            with st.form(key="form_for_basic_info"):
                for item in form_item_list:
                    st.radio(
                        label=st.session_state.system_messages["form"][item]["request"],
                        options=Format_form(item).format_form_options(),
                        format_func=Format_form(item).format_form_choices,
                        key= item,
                        horizontal= True
                    )
                basic_information_submitted = st.form_submit_button()
        if basic_information_submitted:
            st.session_state.user_data["basic_info"] = Format_form.format_form_result(
                args_list=[st.session_state[item] for item in form_item_list]
                )
            st.session_state.memory.append({"role": "assistant", "content": st.session_state.ai_messages["intro"]})
            st.session_state.memory.append({"role": "user", "content": eng_2_ulang.translate(st.session_state.user_data["basic_info"])})
            st.session_state.progress = "information"
            st.rerun()
    
    # phase 2: progress = information
    # 유저한테 조금 더 디테일한 정보 받아옴
    if st.session_state.progress == "information":
        with st.chat_message("assistant"):
            st.write(st.session_state.ai_messages["form_submitted"])
        if st.session_state.user_input_instance:
            st.session_state.user_data["additional_context"] =  st.session_state.user_input_instance
            st.session_state.user_input_instance = ""
            st.rerun()
        if "additional_context" in st.session_state.user_data:
            with st.chat_message("user"):
                st.write(st.session_state.user_data["additional_context_ulang"])
            with st.chat_message("assistant"):
                st.write(st.session_state.ai_messages["check_user_input"])
            user_confirmed = st.button(
                label=st.session_state.user_messages["user_confirmed"],
                use_container_width=True
                )
            if user_confirmed:
                st.session_state.memory.append({"role": "assistant", "content": st.session_state.ai_messages["form_submitted"]})
                st.session_state.memory.append({"role": "user", "content": st.session_state.user_data["additional_context_ulang"]})    
                st.session_state.user_data["symptoms"] = st.session_state.user_data["basic_info"]+"\n"+st.session_state.user_data["additional_context"]
                st.session_state.progress = "chain"
                st.rerun()

    # phase 3: progess = chain
    # 유저에게 모든 필요한 정보를 다 받은 경우. 검색 dataset 크기 조정 후 진단 체인 실행
    if st.session_state.progress in "chain":
        with st.chat_message("assistant"):
            st.write(st.session_state.ai_messages["chain"])
        how_many_search = st.slider(
            label=st.session_state.system_messages["chain"]["num"],
            min_value=5,
            max_value=25,
            value=15,
            step= 1,
        )
        start_diagnosis = st.button(
            label=st.session_state.system_messages["chain"]["start"],
            use_container_width= True
        )
        if start_diagnosis:
            if st.session_state.RAG_prepare == True and chat_model:
                diagnosis_input_dict= {
                    "symptoms" : st.session_state.user_data["symptoms"],
                    "how_many_search" : how_many_search,
                    "faiss_path": faiss_path,
                }
                st.session_state.diagnosis = chat_model.run(
                    purpose= "diagnosis",
                    input= diagnosis_input_dict
                    )
                st.session_state.memory.append({"role": "assistant", "content": eng_2_ulang.translate(st.session_state.diagnosis)})
                st.session_state.progress = "ready_for_chat"
                st.rerun()
            elif st.session_state.RAG_prepare == False:
                st.error(st.session_state.system_messages["RAG"]["error"])
            else:
                st.error(st.session_state.system_messages["model"]["error"])
                st.session_state.model_prepare = False
    
    # phase 3.5: progress = "ready_for_chat"
    # chat 시작 전 세팅 필요하면 이곳에서.
    if st.session_state.progress == "ready_for_chat":
        with st.chat_message("assistant"):
            st.write(st.session_state.system_messages["chat"]["start"])
        start_chat = st.button(
            label=st.session_state.system_messages["chat"]["label"],
            use_container_width= True
        )
        if start_chat:
            st.session_state.progress = "chat"
            st.rerun()

    # phase 4: progress = chat
    # 진단 기반으로 챗봇 구현
    if st.session_state.progress == "chat":
        if chat_model and st.session_state.chat_memory:
            chat_model.add_memory(st.session_state.chat_memory)
        elif st.session_state.chat_memory:
            st.error(st.session_state.system_messages["model"]["error"])
            st.session_state.model_prepare = False
        if st.session_state.user_input_instance:
            chat_input = {
                "symptoms":st.session_state.user_data["symptoms"],
                "query": st.session_state.user_input_instance,
                "diagnosis": st.session_state.diagnosis,
                "faiss_path": faiss_path}
            chat_answer = chat_model.run(
                purpose="chat",
                input= chat_input
            )
            st.session_state.chat_memory.append({"input": st.session_state.user_input_instance, "output": chat_answer})
            st.session_state.memory.append({"role": "user", "content": st.session_state.user_data["chat_input_ulang"]})
            st.session_state.memory.append({"role": "assistant", "content": eng_2_ulang.translate(chat_answer)})
            st.session_state.user_input_instance = ""
            st.rerun()

    # 하단 입력 공간과 대화 초기화 버튼
    User_input_below()
    Clear()


if __name__ == "__main__":
    Setting()
    Sidebar()
    main()
