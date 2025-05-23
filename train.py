import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import os
from model import NeuralNet
from nltk_utils import tokenize, stem, bag_of_words

# Use a relative path so it works on any system
intents_path = os.path.join(os.path.dirname(__file__), "intents.json")

# Load intents
with open(intents_path, 'r') as f:
    intents = json.load(f)

all_words = []
tags = []
xy = []

# Preprocess patterns
for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = tokenize(pattern)
        all_words.extend(w)
        xy.append((w, tag))

ignore_words = ['?', '!', '.', ',']
all_words = sorted(set(stem(w) for w in all_words if w not in ignore_words))
tags = sorted(set(tags))

X_train = []
y_train = []
for (pattern_sentence, tag) in xy:
    bag = bag_of_words(pattern_sentence, all_words)
    X_train.append(bag)
    y_train.append(tags.index(tag))

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.long)

# Dataset
class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train

    def __getitem__(self, index):
        return self.x_data[index], self.y_data[index]

    def __len__(self):
        return self.n_samples

# Hyperparameters
batch_size = 8
hidden_size = 8
input_size = len(X_train[0])
output_size = len(tags)
learning_rate = 0.001
num_epochs = 1000

# Model setup
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = NeuralNet(input_size, hidden_size, output_size).to(device)
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

# Training loop
for epoch in range(num_epochs):
    for words, labels in DataLoader(ChatDataset(), batch_size=batch_size, shuffle=True):
        words, labels = words.to(device), labels.to(device)

        outputs = model(words)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    if (epoch + 1) % 100 == 0:
        print(f"Epoch [{epoch + 1}/{num_epochs}], Loss: {loss.item():.4f}")

# Save model
data = {
    "model_state": model.state_dict(),
    "input_size": input_size,
    "hidden_size": hidden_size,
    "output_size": output_size,
    "all_words": all_words,
    "tags": tags
}

try:
    model_path = os.path.join(os.path.dirname(__file__), "data.pth")
    torch.save(data, model_path)
    print(f"✅ Training complete. File saved as: {model_path}")
except Exception as e:
    print(f"❌ Failed to save model: {e}")
