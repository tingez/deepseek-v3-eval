import streamlit as st
import json
import pandas as pd
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Email Analysis Comparison",
    layout="wide"
)

def load_json_data(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

# Load data
openai_data = load_json_data('analyzed_emails_openai.json')
deepseek_data = load_json_data('analyzed_emails_deepseek.json')
llama_data = load_json_data('analyzed_emails_llama.json')
qwen_data = load_json_data('analyzed_emails_qwen.json')

if not openai_data:
    st.error("Failed to load OpenAI data")
    st.stop()

# Create summary table
def create_summary(data):
    if not data:
        return {}
    
    total_emails = len(data)
    unique_labels = set()
    for item in data.values():
        unique_labels.update(item.get('post_labels', []))
    
    return {
        'Total Emails': total_emails,
        'Unique Labels': len(unique_labels),
        'Label Categories': ', '.join(sorted(unique_labels))
    }

summary_data = {
    'OpenAI': create_summary(openai_data),
    'DeepSeek': create_summary(deepseek_data),
    'Llama': create_summary(llama_data),
    'Qwen': create_summary(qwen_data)
}

# Initialize selection counts in session state
if 'model_selection_counts' not in st.session_state:
    st.session_state.model_selection_counts = {
        'OpenAI': 0,
        'DeepSeek': 0,
        'Llama': 0,
        'Qwen': 0
    }

def save_selection_summary():
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_emails_compared': len(st.session_state.better_choices),
        'model_counts': st.session_state.model_selection_counts,
        'detailed_selections': st.session_state.better_choices
    }
    try:
        with open('selection_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
    except Exception as e:
        print(f"Error saving selection summary: {str(e)}")
        print(traceback.format_exc())

st.title("Email Analysis Comparison")

# Display summary table
st.subheader("Summary Information")
summary_df = pd.DataFrame(summary_data)
st.table(summary_df)

# Display current selection counts
st.subheader("Current Selection Counts")
counts_df = pd.DataFrame([st.session_state.model_selection_counts])
st.table(counts_df)

# Create comparison view
st.subheader("Detailed Comparison")

# Get common email IDs
email_ids = set(openai_data.keys())
if deepseek_data:
    email_ids = email_ids.intersection(deepseek_data.keys())
if llama_data:
    email_ids = email_ids.intersection(llama_data.keys())
if qwen_data:
    email_ids = email_ids.intersection(qwen_data.keys())

email_ids = sorted(email_ids)
total_emails = len(email_ids)

def display_email(email):
    fields = [
        ('Email ID', 'email_id', None),
        ('Labels', 'post_labels', lambda x: ", ".join(x) if x else ""),
        ('Content (CN)', 'post_content_cn', None),
        ('Content (EN)', 'post_content_en', None),
        ('Links', 'link_lists', lambda x: "\n".join(x) if x else ""),
        ('Summary (CN)', 'post_summary_cn', None),
        ('Summary (EN)', 'post_summary_en', None),
        ('Date Time', 'post_datetime', None),
        ('Source Language', 'source_language', None),
        ('Confidence Score', 'confidence_score', None)
    ]
    
    for label, field, transform in fields:
        value = email.get(field, '')
        if value:
            if transform:
                value = transform(value)
            st.write(f"**{label}:**", value)

# Display progress
st.subheader("Progress")
st.write(f"Showing emails: {total_emails} total")
progress = st.progress(0)

# Initialize better_choices if not exists
if 'better_choices' not in st.session_state:
    st.session_state.better_choices = {}

# Display data in columns
for idx, email_id in enumerate(email_ids, 1):
    # Update progress
    progress.progress(idx / total_emails)
    
    st.markdown(f"#### Email #{idx}/{total_emails} - ID: {email_id}")
    
    # Create four columns for comparison
    cols = st.columns(4)
    
    # Display data in columns
    models_data = [
        ("OpenAI Analysis", openai_data, 0),
        ("DeepSeek Analysis", deepseek_data, 1),
        ("Llama Analysis", llama_data, 2),
        ("Qwen Analysis", qwen_data, 3)
    ]
    
    for title, data, col_idx in models_data:
        with cols[col_idx]:
            st.markdown(f"**{title}**")
            if data and email_id in data:
                display_email(data[email_id])
    
    # Add checkboxes for multiple selection
    st.write("**Select better analyses:**")
    checkbox_cols = st.columns(4)
    
    key = f"better_choice_{email_id}"
    if key not in st.session_state.better_choices:
        st.session_state.better_choices[key] = []
    
    selected_models = []
    for model, col in zip(['OpenAI', 'DeepSeek', 'Llama', 'Qwen'], checkbox_cols):
        with col:
            if st.checkbox(
                model,
                value=model in st.session_state.better_choices[key],
                key=f"{key}_{model}"
            ):
                selected_models.append(model)
    
    # Update selection counts and save to file
    if selected_models != st.session_state.better_choices[key]:
        # Remove old counts
        for model in st.session_state.better_choices[key]:
            st.session_state.model_selection_counts[model] -= 1
        
        # Add new counts
        for model in selected_models:
            st.session_state.model_selection_counts[model] += 1
        
        # Update choices and save
        st.session_state.better_choices[key] = selected_models
        save_selection_summary()
    
    st.markdown("---")  # Add separator between entries
