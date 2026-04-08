/**
 * SoloSessionScreen — private chat with Agent A or Agent B.
 *
 * Connects to POST /v1/agent-a/chat or /v1/agent-b/chat depending on
 * the agentRole navigation param. Messages are stored in the backend's
 * private pgvector namespace and never accessible to the other partner.
 */

import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '../../App';
import { ChatBubble, BubbleSender } from '../components/ChatBubble';
import { trinityAPI } from '../services/api';

type Props = NativeStackScreenProps<RootStackParamList, 'SoloSession'>;

interface Message {
  id: string;
  text: string;
  sender: BubbleSender;
  timestamp: string;
}

export function SoloSessionScreen({ route }: Props) {
  const { agentRole, partnerName } = route.params;
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      text: `Hello ${partnerName}. This is your private space. Nothing you share here is shown to your partner. How are you today?`,
      sender: 'agent',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const sendMessage = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputText('');
    setIsLoading(true);

    try {
      const chatFn = agentRole === 'agent_a' ? trinityAPI.agentAChat : trinityAPI.agentBChat;
      const result = await chatFn.call(trinityAPI, text, partnerName);

      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: result.response,
        sender: result.crisis_detected ? 'crisis' : 'agent',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm having trouble connecting right now. Please try again in a moment.",
        sender: 'agent',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, agentRole, partnerName]);

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={88}
    >
      <View style={styles.privacyBanner}>
        <Text style={styles.privacyText}>🔒 Private session — visible only to you</Text>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ChatBubble text={item.text} sender={item.sender} timestamp={item.timestamp} />
        )}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      {isLoading && (
        <View style={styles.typingIndicator}>
          <ActivityIndicator size="small" color="#4a4a8a" />
          <Text style={styles.typingText}>thinking...</Text>
        </View>
      )}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="What's on your mind?"
          placeholderTextColor="#bbb"
          multiline
          maxLength={2000}
          onSubmitEditing={sendMessage}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!inputText.trim() || isLoading) && styles.sendButtonDisabled]}
          onPress={sendMessage}
          disabled={!inputText.trim() || isLoading}
        >
          <Text style={styles.sendButtonText}>↑</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f9f5f0' },
  privacyBanner: {
    backgroundColor: '#e8f4e8', paddingVertical: 6, paddingHorizontal: 16,
    borderBottomWidth: 1, borderBottomColor: '#d0e8d0',
  },
  privacyText: { fontSize: 12, color: '#3a7a3a', textAlign: 'center' },
  messageList: { paddingVertical: 12, paddingBottom: 4 },
  typingIndicator: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 6, gap: 6 },
  typingText: { fontSize: 13, color: '#888', fontStyle: 'italic' },
  inputRow: {
    flexDirection: 'row', alignItems: 'flex-end', paddingHorizontal: 12,
    paddingVertical: 10, borderTopWidth: 1, borderTopColor: '#e8e0d8',
    backgroundColor: '#ffffff', gap: 8,
  },
  input: {
    flex: 1, backgroundColor: '#f4f0ec', borderRadius: 22,
    paddingHorizontal: 16, paddingVertical: 10, fontSize: 15, color: '#1a1a2e',
    maxHeight: 120, borderWidth: 1, borderColor: '#e0d8d0',
  },
  sendButton: {
    width: 44, height: 44, borderRadius: 22, backgroundColor: '#4a4a8a',
    alignItems: 'center', justifyContent: 'center',
  },
  sendButtonDisabled: { backgroundColor: '#c0c0d8' },
  sendButtonText: { color: '#ffffff', fontSize: 20, fontWeight: '600' },
});
