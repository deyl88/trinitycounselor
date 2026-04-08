/**
 * OnboardingScreen — entry point for new users.
 *
 * TODO: This is a stub. Full implementation will include:
 *   - Partner registration (email + password)
 *   - Relationship creation (invite partner)
 *   - Attachment style intake questionnaire
 *   - Informed consent + privacy explanation
 */

import React, { useState } from 'react';
import {
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

type Props = NativeStackScreenProps<RootStackParamList, 'Onboarding'>;

export function OnboardingScreen({ navigation }: Props) {
  const [name, setName] = useState('');
  const [role, setRole] = useState<'partner_a' | 'partner_b'>('partner_a');

  const handleStart = () => {
    if (!name.trim()) return;
    navigation.navigate('SoloSession', {
      agentRole: role,
      partnerName: name.trim(),
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.logo}>Trinity</Text>
        <Text style={styles.tagline}>
          A private space for you.{'\n'}A shared space for your relationship.
        </Text>

        <View style={styles.form}>
          <Text style={styles.label}>Your first name</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Alex"
            placeholderTextColor="#bbb"
            autoCapitalize="words"
          />

          <Text style={styles.label}>I am</Text>
          <View style={styles.roleSelector}>
            {(['partner_a', 'partner_b'] as const).map((r) => (
              <TouchableOpacity
                key={r}
                style={[styles.roleButton, role === r && styles.roleButtonActive]}
                onPress={() => setRole(r)}
              >
                <Text style={[styles.roleText, role === r && styles.roleTextActive]}>
                  {r === 'partner_a' ? 'Partner A' : 'Partner B'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity
            style={[styles.startButton, !name.trim() && styles.startButtonDisabled]}
            onPress={handleStart}
            disabled={!name.trim()}
          >
            <Text style={styles.startButtonText}>Begin My Private Session</Text>
          </TouchableOpacity>
        </View>

        <Text style={styles.privacy}>
          Your private sessions are encrypted and never shared with your partner.
          Only abstracted patterns flow into the shared relationship space.
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#1a1a2e' },
  content: { flex: 1, justifyContent: 'center', paddingHorizontal: 28 },
  logo: { fontSize: 48, fontWeight: '700', color: '#e8d5b7', textAlign: 'center', marginBottom: 8 },
  tagline: { fontSize: 16, color: '#a0a0c0', textAlign: 'center', lineHeight: 24, marginBottom: 40 },
  form: { gap: 12 },
  label: { fontSize: 14, color: '#c0c0d8', fontWeight: '500' },
  input: {
    backgroundColor: '#2a2a4a', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 14,
    fontSize: 16, color: '#e8d5b7', borderWidth: 1, borderColor: '#3a3a5a',
  },
  roleSelector: { flexDirection: 'row', gap: 12 },
  roleButton: {
    flex: 1, paddingVertical: 12, borderRadius: 10, borderWidth: 1,
    borderColor: '#3a3a5a', alignItems: 'center',
  },
  roleButtonActive: { backgroundColor: '#4a4a8a', borderColor: '#6a6aaa' },
  roleText: { color: '#a0a0c0', fontWeight: '500' },
  roleTextActive: { color: '#ffffff' },
  startButton: {
    marginTop: 8, backgroundColor: '#6a6aaa', borderRadius: 12,
    paddingVertical: 16, alignItems: 'center',
  },
  startButtonDisabled: { opacity: 0.5 },
  startButtonText: { color: '#ffffff', fontSize: 16, fontWeight: '600' },
  privacy: { marginTop: 32, fontSize: 12, color: '#606080', textAlign: 'center', lineHeight: 18 },
});
