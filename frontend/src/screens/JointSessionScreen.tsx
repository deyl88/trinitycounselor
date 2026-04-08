/**
 * JointSessionScreen — mediated session with Agent R.
 *
 * Both partners participate; messages are mediated by the Relationship
 * Counselor (Agent R) which has access to the RKG but NOT to either
 * partner's private conversation history.
 *
 * TODO: This is a stub. Full implementation will include:
 *   - Real-time sync between both partners' devices (WebSocket)
 *   - Partner presence indicators
 *   - "Speak" / "Listen" turn management
 *   - Therapist-initiated check-ins
 */

import React, { useRef, useState } from 'react';
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

type Props = NativeStackScreenProps<RootStackParamList, 'JointSession'>;

interface Message {
  id: string;
  text: string;
  sender: BubbleSender;
  label?: string;
  timestamp: string;
}

export function JointSessionScreen({ route }: Props) {
  const { relationshipId } = route.params;
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '0',
      text: "Welcome to your shared space. I'm here to hold this conversation with both of you. Neither of your private sessions are visible here — only what you each choose to share right now.",
      sender: 'agent',
      label: 'Relationship Counselor',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  const sendMessage = async () => {
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
      // In a full implementation, partnerAMessage vs partnerBMessage is determined
      // by the current user's partner_tag from their JWT.
      const result = await trinityAPI.agentRJoint(text, undefined);

      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: result.response,
        sender: result.crisis_detected ? 'crisis' : 'agent',
        label: 'Relationship Counselor',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, agentMsg]);
    } catch {
      const errMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: "I'm having trouble connecting right now. Please try again.",
        sender: 'agent',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={88}
    >
      <View style={styles.sessionHeader}>
        <Text style={styles.headerTitle}>Joint Session</Text>
        <Text style={styles.headerSub}>Mediated by your Relationship Counselor</Text>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View>
            {item.label && item.sender !== 'user' && (
              <Text style={styles.senderLabel}>{item.label}</Text>
            )}
            <ChatBubble text={item.text} sender={item.sender} timestamp={item.timestamp} />
          </View>
        )}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      {isLoading && (
        <View style={styles.typingIndicator}>
          <ActivityIndicator size="small" color="#8a4a8a" />
          <Text style={styles.typingText}>Relationship Counselor is responding...</Text>
        </View>
      )}

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Share what's true for you right now..."
          placeholderTextColor="#bbb"
          multiline
          maxLength={2000}
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
  sessionHeader: {
    backgroundColor: '#2a1a2e', paddingVertical: 12, paddingHorizontal: 16, alignItems: 'center',
  },
  headerTitle: { fontSize: 16, fontWeight: '600', color: '#e8d5b7' },
  headerSub: { fontSize: 12, color: '#a090b0', marginTop: 2 },
  messageList: { paddingVertical: 12 },
  senderLabel: { fontSize: 11, color: '#8a6a8a', paddingLeft: 24, paddingTop: 8, fontWeight: '500' },
  typingIndicator: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 6, gap: 6 },
  typingText: { fontSize: 13, color: '#8a6a8a', fontStyle: 'italic' },
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
    width: 44, height: 44, borderRadius: 22, backgroundColor: '#8a4a8a',
    alignItems: 'center', justifyContent: 'center',
  },
  sendButtonDisabled: { backgroundColor: '#c0a0c0' },
  sendButtonText: { color: '#ffffff', fontSize: 20, fontWeight: '600' },
});
