import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

export type BubbleSender = 'user' | 'agent' | 'crisis';

interface ChatBubbleProps {
  text: string;
  sender: BubbleSender;
  timestamp?: string;
}

export function ChatBubble({ text, sender, timestamp }: ChatBubbleProps) {
  const isUser = sender === 'user';
  const isCrisis = sender === 'crisis';

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.agentContainer]}>
      <View
        style={[
          styles.bubble,
          isUser ? styles.userBubble : styles.agentBubble,
          isCrisis && styles.crisisBubble,
        ]}
      >
        <Text style={[styles.text, isUser ? styles.userText : styles.agentText]}>
          {text}
        </Text>
        {timestamp && (
          <Text style={styles.timestamp}>{timestamp}</Text>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    marginHorizontal: 12,
    flexDirection: 'row',
  },
  userContainer: {
    justifyContent: 'flex-end',
  },
  agentContainer: {
    justifyContent: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    borderRadius: 18,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  userBubble: {
    backgroundColor: '#4a4a8a',
    borderBottomRightRadius: 4,
  },
  agentBubble: {
    backgroundColor: '#ffffff',
    borderBottomLeftRadius: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
    elevation: 1,
  },
  crisisBubble: {
    backgroundColor: '#fff3cd',
    borderColor: '#e6a817',
    borderWidth: 1,
  },
  text: {
    fontSize: 15,
    lineHeight: 22,
  },
  userText: {
    color: '#ffffff',
  },
  agentText: {
    color: '#1a1a2e',
  },
  timestamp: {
    fontSize: 11,
    color: '#999',
    marginTop: 4,
    alignSelf: 'flex-end',
  },
});
