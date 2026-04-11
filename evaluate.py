from nlu import parse_command
from logger import log

labels = [
    "OPEN_BROWSER",
    "CREATE_FOLDER",
    "GET_TIME",
    "SEARCH_GOOGLE",
    "SET_VOLUME",
    "OPEN_APP_DYNAMIC",
    "UNKNOWN"
]

test_commands = [

# OPEN_BROWSER
("open chrome", "OPEN_BROWSER"),
("open browser", "OPEN_BROWSER"),
("chrome open", "OPEN_BROWSER"),
("launch browser", "OPEN_BROWSER"),
("start chrome", "OPEN_BROWSER"),

# CREATE_FOLDER
("create folder test", "CREATE_FOLDER"),
("create new folder", "CREATE_FOLDER"),
("make new folder", "CREATE_FOLDER"),
("make folder", "CREATE_FOLDER"),
("new folder create", "CREATE_FOLDER"),

# GET_TIME
("what time is it", "GET_TIME"),
("tell me the time", "GET_TIME"),
("current time", "GET_TIME"),
("time now", "GET_TIME"),
("what is time", "GET_TIME"),

# SEARCH_GOOGLE
("search python", "SEARCH_GOOGLE"),
("google python", "SEARCH_GOOGLE"),
("search ai tools", "SEARCH_GOOGLE"),
("google machine learning", "SEARCH_GOOGLE"),
("search data science", "SEARCH_GOOGLE"),

# SET_VOLUME
("set volume 50", "SET_VOLUME"),
("volume to 30", "SET_VOLUME"),
("change volume to 80", "SET_VOLUME"),
("set volume 20", "SET_VOLUME"),
("volume 60", "SET_VOLUME"),

# OPEN_APP_DYNAMIC
("open calculator", "OPEN_APP_DYNAMIC"),
("open notepad", "OPEN_APP_DYNAMIC"),
("open vscode", "OPEN_APP_DYNAMIC"),
("open spotify", "OPEN_APP_DYNAMIC"),
("open settings", "OPEN_APP_DYNAMIC"),

# UNKNOWN
("random words", "UNKNOWN"),
("asdfgh", "UNKNOWN"),
("hello there", "UNKNOWN"),
("blah blah", "UNKNOWN"),
("nothing command", "UNKNOWN"),

# OPEN_BROWSER
("ക്രോം തുറക്കൂ", "OPEN_BROWSER"),
("ബ്രൗസർ തുറക്കൂ", "OPEN_BROWSER"),

# CREATE_FOLDER
("ഒരു ഫോൾഡർ ഉണ്ടാക്കൂ", "CREATE_FOLDER"),
("പുതിയ ഫോൾഡർ സൃഷ്ടിക്കൂ", "CREATE_FOLDER"),

# GET_TIME
("ഇപ്പോൾ സമയം എന്താണ്", "GET_TIME"),
("സമയം പറയൂ", "GET_TIME"),

# SEARCH_GOOGLE
("ഗൂഗിളിൽ പൈത്തൺ തിരയൂ", "SEARCH_GOOGLE"),
("എഐ ടൂളുകൾ തിരയൂ", "SEARCH_GOOGLE"),

# SET_VOLUME
("വോള്യം 50 ആക്കൂ", "SET_VOLUME"),
("ശബ്ദം കുറയ്ക്കൂ", "SET_VOLUME"),

# OPEN_APP_DYNAMIC
("കാൽക്കുലേറ്റർ തുറക്കൂ", "OPEN_APP_DYNAMIC"),
("നോട്ട്‌പാഡ് തുറക്കൂ", "OPEN_APP_DYNAMIC"),

# UNKNOWN
("ചെയ്തുകൊടുത്തതും പ്രത്യയില്ല", "UNKNOWN"),
("ചെയ്തുകൊടുത്തതും പ്രത്യയില്ല", "UNKNOWN"),

# OPEN_BROWSER
("chrome thurakku", "OPEN_BROWSER"),
("browser open cheyyu", "OPEN_BROWSER"),

# CREATE_FOLDER
("new folder undakku", "CREATE_FOLDER"),
("oru folder create cheyyu", "CREATE_FOLDER"),

# GET_TIME
("time entha", "GET_TIME"),
("ippo time para", "GET_TIME"),

# SEARCH_GOOGLE
("google il python search cheyyu", "SEARCH_GOOGLE"),
("ai tools search cheyyu", "SEARCH_GOOGLE"),

# SET_VOLUME
("volume 50 aakku", "SET_VOLUME"),
("sound kurakku", "SET_VOLUME"),

# OPEN_APP_DYNAMIC
("calculator thurakku", "OPEN_APP_DYNAMIC"),
("notepad open cheyyu", "OPEN_APP_DYNAMIC"),

# messy / real inputs
("can you open chrome please", "OPEN_BROWSER"),
("uh open browser", "OPEN_BROWSER"),
("please create a folder named test", "CREATE_FOLDER"),
("hey whats the time now", "GET_TIME"),
("search for python tutorials", "SEARCH_GOOGLE"),
("set volume to like 40", "SET_VOLUME"),
("open my calculator app", "OPEN_APP_DYNAMIC"),

]

actual = []
predicted = []

for text, expected in test_commands:
    result = parse_command(text)

    actual.append(expected)
    if isinstance(result.name, tuple):
        predicted.append(result.name[0])
    else:
        predicted.append(result.name)  

print("\nDEBUG:")
for a, p in zip(actual, predicted):
    print(a, "->", p)

from sklearn.metrics import confusion_matrix
import pandas as pd

cm = confusion_matrix(actual, predicted, labels=labels)

df = pd.DataFrame(cm, index=labels, columns=labels)

print("\nConfusion Matrix:\n")
print(df)

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

accuracy = accuracy_score(actual, predicted)
precision = precision_score(actual, predicted, average='weighted', zero_division=0)
recall = recall_score(actual, predicted, average='weighted', zero_division=0)
f1 = f1_score(actual, predicted, average='weighted', zero_division=0)

print("\nMetrics:")
print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)

import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(8,6))
sns.heatmap(df, annot=True, fmt="d", cmap="Blues")

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Voice Intent Confusion Matrix")

plt.savefig("voice_confusion_matrix.png")
plt.show()


from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

# Labels (IMPORTANT: fixed order)
labels = ["CLICK", "MOVE", "SCROLL", "NONE"]

# Actual gestures
gesture_actual = [
    "CLICK","CLICK","CLICK","CLICK","CLICK",
    "MOVE","MOVE","MOVE","MOVE","MOVE",
    "SCROLL","SCROLL","SCROLL","SCROLL","SCROLL",
    "NONE","NONE","NONE","NONE","NONE"
]

# Predicted gestures (from your system)
gesture_predicted = [
    "CLICK","MOVE","MOVE","SCROLL","NONE",
    "MOVE","MOVE","MOVE","MOVE","MOVE",
    "SCROLL","SCROLL","SCROLL","SCROLL","SCROLL",
    "NONE","NONE","NONE","NONE","NONE"
]

# Confusion Matrix
cm = confusion_matrix(gesture_actual, gesture_predicted, labels=labels)

# Convert to DataFrame for better visualization
df_cm = pd.DataFrame(cm, index=labels, columns=labels)

print("\nGesture Confusion Matrix:\n")
print(df_cm)

# Metrics
accuracy = accuracy_score(gesture_actual, gesture_predicted)
precision = precision_score(gesture_actual, gesture_predicted, average="weighted")
recall = recall_score(gesture_actual, gesture_predicted, average="weighted")
f1 = f1_score(gesture_actual, gesture_predicted, average="weighted")

print("\nGesture Metrics:")
print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)

# Plot
plt.figure(figsize=(8,6))
sns.heatmap(df_cm, annot=True, fmt="d", cmap="Blues")

plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Gesture Confusion Matrix")

plt.savefig("gesture_confusion_matrix.png")
plt.show()