import os
import re
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# Load all .html files
files = [f for f in os.listdir() if f.endswith('.html')]
messages = []

def is_system_message(text):
    system_keywords = [
        "Messages you send to this chat are now secured",
        "changed the subject", "created group", "added", "left", "removed"
    ]
    return any(kw in text for kw in system_keywords)

# Step 1: Extract messages
for filename in files:
    with open(filename, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')
        for p in soup.find_all('p'):
            text = p.get_text()
            match = re.match(r"\[(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}(?::\d{2})?)\] (.*?): (.*)", text)
            if match:
                date, time, sender, msg = match.groups()
                dt_str = f"{date} {time}"
                try:
                    dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                except:
                    try:
                        dt = datetime.strptime(dt_str, "%d/%m/%Y %H:%M")
                    except:
                        continue
                if not is_system_message(msg):
                    messages.append({'datetime': dt, 'sender': sender, 'text': msg.strip()})

# Step 2: Detect events
df = pd.DataFrame(messages)
df.sort_values('datetime', inplace=True)

events = []
keywords = [
    'love', 'jealous', 'sorry', 'cry', 'gift', 'movie', 'fight', 'hate', 
    'block', 'unblock', 'trust', 'miss', 'care', 'angry', 'emotional', 
    'hurt', 'happy', 'sad', 'talk', 'alone', 'feelings', 'relationship'
]

visited = set()
for i in range(len(df)):
    if i in visited:
        continue
    start = df.iloc[i]['datetime']
    for days in [1, 2, 3]:
        end = start + timedelta(days=days)
        window = df[(df['datetime'] >= start) & (df['datetime'] <= end)]
        if len(window) >= 16:
            blob = ' '.join(window['text'].tolist()).lower()
            if any(k in blob for k in keywords):
                if not any(e['start'] <= end and e['end'] >= start for e in events):
                    events.append({'start': start, 'end': end, 'messages': window.copy()})
                    visited.update(window.index)

# Step 3: Summarize events
rows = []
for evt in events:
    texts = ' '.join(evt['messages']['text']).lower()
    msg_count = len(evt['messages'])
    first_line = evt['messages'].iloc[0]['text']
    start_str = evt['start'].strftime('%b %d, %Y')
    end_str = evt['end'].strftime('%b %d, %Y')

    # Memory type
    if 'cry' in texts or 'hurt' in texts:
        memory_type = 'Emotional Memory'
    elif 'love' in texts or 'gift' in texts or 'miss' in texts:
        memory_type = 'Good Memory'
    elif 'fight' in texts or 'block' in texts or 'jealous' in texts:
        memory_type = 'Mixed Memory'
    else:
        memory_type = 'Casual/Funny Memory'

    # Title guess
    if 'block' in texts:
        title = 'Blocking Incident'
    elif 'fight' in texts or 'angry' in texts:
        title = 'Argument or Fight'
    elif 'gift' in texts or 'movie' in texts:
        title = 'Romantic Plan'
    elif 'jealous' in texts:
        title = 'Jealousy or Insecurity'
    elif 'cry' in texts:
        title = 'Emotional Breakdown'
    else:
        title = 'Relationship Talk'

    rows.append({
        "🏷️ Event Title": title,
        "📅 Date Range": f"{start_str} – {end_str}",
        "🧠 Memory Type": memory_type,
        "📝 Detailed Summary": f"{msg_count} emotional messages exchanged between {start_str} and {end_str}.",
        "💬 Special Quotes": first_line
    })

# Step 4: Export to Excel
df_out = pd.DataFrame(rows)
df_out.to_excel("relationship_events.xlsx", index=False)
print("✅ Exported to 'relationship_events.xlsx'")
