import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StatusBar } from 'expo-status-bar';

import { OnboardingScreen } from '@/screens/OnboardingScreen';
import { SoloSessionScreen } from '@/screens/SoloSessionScreen';
import { JointSessionScreen } from '@/screens/JointSessionScreen';

export type RootStackParamList = {
  Onboarding: undefined;
  SoloSession: { agentRole: 'agent_a' | 'agent_b'; partnerName: string };
  JointSession: { relationshipId: string };
};

const Stack = createStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        initialRouteName="Onboarding"
        screenOptions={{
          headerStyle: { backgroundColor: '#1a1a2e' },
          headerTintColor: '#e8d5b7',
          headerTitleStyle: { fontWeight: '600' },
          cardStyle: { backgroundColor: '#f9f5f0' },
        }}
      >
        <Stack.Screen
          name="Onboarding"
          component={OnboardingScreen}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="SoloSession"
          component={SoloSessionScreen}
          options={{ title: 'Your Private Space' }}
        />
        <Stack.Screen
          name="JointSession"
          component={JointSessionScreen}
          options={{ title: 'Together' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
