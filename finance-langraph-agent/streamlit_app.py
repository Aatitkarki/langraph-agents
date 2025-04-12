import streamlit as st
from finance_agent import app
from langchain_core.messages import HumanMessage, AIMessage

st.title("Finance Agent")
query = st.text_input("Enter your query:")

if st.button("Submit"):
    # Call the finance agent here and display the result
    initial_state = {"messages": [HumanMessage(content=query)]}
    result = app.invoke(initial_state)
    
    # Extract the content of the AIMessage
    if "messages" in result and len(result["messages"]) > 0:
        last_message = result["messages"][-1]
        if isinstance(last_message, AIMessage):
            st.write(last_message.content)
        else:
            st.write("Unexpected response type: " + str(type(last_message)))
    else:
        st.write("No response received.")

# UI elements will be added here