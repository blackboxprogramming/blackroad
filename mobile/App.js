import React, { useEffect, useState } from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { createNativeStackNavigator } from '@react-navigation/stack'
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs'
import { Ionicons } from '@expo/vector-icons'
import { StatusBar } from 'expo-status-bar'

// Screens
import LoginScreen from './src/screens/LoginScreen'
import DashboardScreen from './src/screens/DashboardScreen'
import AnalyticsScreen from './src/screens/AnalyticsScreen'
import BillingScreen from './src/screens/BillingScreen'
import SettingsScreen from './src/screens/SettingsScreen'

const Stack = createNativeStackNavigator()
const Tab = createBottomTabNavigator()

function DashboardTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName

          if (route.name === 'Dashboard') {
            iconName = focused ? 'home' : 'home-outline'
          } else if (route.name === 'Analytics') {
            iconName = focused ? 'bar-chart' : 'bar-chart-outline'
          } else if (route.name === 'Billing') {
            iconName = focused ? 'card' : 'card-outline'
          } else if (route.name === 'Settings') {
            iconName = focused ? 'settings' : 'settings-outline'
          }

          return <Ionicons name={iconName} size={size} color={color} />
        },
        tabBarActiveTintColor: '#667eea',
        tabBarInactiveTintColor: '#999',
        headerStyle: {
          backgroundColor: '#667eea',
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Analytics" component={AnalyticsScreen} />
      <Tab.Screen name="Billing" component={BillingScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  )
}

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in (check AsyncStorage)
    const checkAuth = async () => {
      // Will be implemented with AsyncStorage
      setLoading(false)
    }
    checkAuth()
  }, [])

  if (loading) {
    return null
  }

  return (
    <>
      <StatusBar barStyle="light-content" backgroundColor="#667eea" />
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerShown: false,
          }}
        >
          {!isLoggedIn ? (
            <Stack.Screen 
              name="Login" 
              component={LoginScreen}
              listeners={({ navigation }) => ({
                tabPress: (e) => {
                  e.preventDefault()
                },
              })}
            />
          ) : (
            <Stack.Screen name="Main" component={DashboardTabs} />
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </>
  )
}
