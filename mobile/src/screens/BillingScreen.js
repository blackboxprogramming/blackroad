import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'

export default function BillingScreen() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [activeTab, setActiveTab] = useState('current')

  const fetchData = async () => {
    try {
      setData({
        plan: {
          name: 'Light',
          price: 25,
          nextBillingDate: '2026-06-04',
        },
        usage: {
          requests: 12500,
          included: 50000,
          forecast: 25.00,
        },
        invoices: [
          { id: 'INV-001', date: '2026-04-04', amount: 25, status: 'paid' },
          { id: 'INV-002', date: '2026-03-04', amount: 22.50, status: 'paid' },
          { id: 'INV-003', date: '2026-02-04', amount: 18.75, status: 'paid' },
        ],
      })
    } catch (error) {
      console.error(error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const onRefresh = () => {
    setRefreshing(true)
    fetchData()
  }

  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color="#667eea" />
      </View>
    )
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      {/* Current Plan */}
      <View style={styles.planCard}>
        <View style={styles.planHeader}>
          <Text style={styles.planName}>{data?.plan.name}</Text>
          <Text style={styles.planBadge}>Active</Text>
        </View>
        <Text style={styles.planPrice}>${data?.plan.price}<Text style={styles.planPeriod}>/month</Text></Text>
        <Text style={styles.planDate}>
          Next billing: {new Date(data?.plan.nextBillingDate).toLocaleDateString()}
        </Text>
        <TouchableOpacity style={styles.upgradeButton}>
          <Text style={styles.upgradeButtonText}>Upgrade Plan</Text>
        </TouchableOpacity>
      </View>

      {/* Usage Info */}
      <View style={styles.usageCard}>
        <View style={styles.usageRow}>
          <View>
            <Text style={styles.usageLabel}>Requests This Month</Text>
            <Text style={styles.usageValue}>{data?.usage.requests.toLocaleString()}</Text>
          </View>
          <View>
            <Text style={styles.usageLabel}>Included</Text>
            <Text style={styles.usageValue}>{data?.usage.included.toLocaleString()}</Text>
          </View>
        </View>
        <View style={styles.progressBar}>
          <View style={[styles.progressFill, { width: '25%' }]} />
        </View>
        <Text style={styles.usageHint}>You're well within your monthly limit</Text>
      </View>

      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'current' && styles.activeTab]}
          onPress={() => setActiveTab('current')}
        >
          <Text style={[styles.tabText, activeTab === 'current' && styles.activeTabText]}>
            Current Month
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'invoices' && styles.activeTab]}
          onPress={() => setActiveTab('invoices')}
        >
          <Text style={[styles.tabText, activeTab === 'invoices' && styles.activeTabText]}>
            History
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      {activeTab === 'invoices' && (
        <View style={styles.invoiceList}>
          {data?.invoices.map((invoice, index) => (
            <View key={index} style={styles.invoiceRow}>
              <View style={styles.invoiceInfo}>
                <Text style={styles.invoiceId}>{invoice.id}</Text>
                <Text style={styles.invoiceDate}>
                  {new Date(invoice.date).toLocaleDateString()}
                </Text>
              </View>
              <View style={styles.invoiceRight}>
                <Text style={styles.invoiceAmount}>${invoice.amount.toFixed(2)}</Text>
                <View style={styles.invoiceStatus}>
                  <Text style={styles.invoiceStatusText}>{invoice.status}</Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  planCard: {
    margin: 12,
    backgroundColor: '#667eea',
    borderRadius: 8,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  planBadge: {
    backgroundColor: 'rgba(255,255,255,0.3)',
    color: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
    fontSize: 12,
    fontWeight: '600',
  },
  planPrice: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
  },
  planPeriod: {
    fontSize: 16,
  },
  planDate: {
    color: 'rgba(255,255,255,0.8)',
    marginTop: 8,
    marginBottom: 16,
  },
  upgradeButton: {
    backgroundColor: '#fff',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 6,
    alignItems: 'center',
    marginTop: 12,
  },
  upgradeButtonText: {
    color: '#667eea',
    fontWeight: 'bold',
    fontSize: 14,
  },
  usageCard: {
    margin: 12,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  usageRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  usageLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  usageValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#667eea',
  },
  usageHint: {
    fontSize: 12,
    color: '#2ecc71',
  },
  tabs: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
    paddingHorizontal: 12,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
    alignItems: 'center',
  },
  activeTab: {
    borderBottomColor: '#667eea',
  },
  tabText: {
    fontSize: 14,
    color: '#999',
    fontWeight: '600',
  },
  activeTabText: {
    color: '#667eea',
  },
  invoiceList: {
    padding: 12,
  },
  invoiceRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  invoiceInfo: {
    flex: 1,
  },
  invoiceId: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  invoiceDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  invoiceRight: {
    alignItems: 'flex-end',
  },
  invoiceAmount: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  invoiceStatus: {
    marginTop: 4,
    backgroundColor: '#2ecc71',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  invoiceStatusText: {
    fontSize: 10,
    color: '#fff',
    fontWeight: 'bold',
  },
})
