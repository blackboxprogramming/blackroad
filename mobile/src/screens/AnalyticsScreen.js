import React, { useState, useEffect } from 'react'
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native'
import { Ionicons } from '@expo/vector-icons'

export default function AnalyticsScreen() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = async () => {
    try {
      setData({
        churnRisk: { high: 7, medium: 15, low: 78 },
        ltv: 920,
        segments: [
          { name: 'Enterprise', count: 12, growth: '+8%' },
          { name: 'Mid-Market', count: 45, growth: '+12%' },
          { name: 'SMB', count: 143, growth: '+25%' },
          { name: 'Starter', count: 289, growth: '-3%' },
        ],
        metrics: {
          avgResponseTime: 245,
          errorRate: 0.12,
          p95Latency: 890,
        },
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
      {/* Performance Metrics */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Performance</Text>
        <View style={styles.metricRow}>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Avg Response</Text>
            <Text style={styles.metricValue}>{data?.metrics.avgResponseTime}ms</Text>
          </View>
          <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>Error Rate</Text>
            <Text style={[styles.metricValue, { color: '#e74c3c' }]}>
              {(data?.metrics.errorRate * 100).toFixed(2)}%
            </Text>
          </View>
        </View>
      </View>

      {/* LTV Forecast */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>LTV Forecast</Text>
          <Ionicons name="trending-up" size={20} color="#667eea" />
        </View>
        <View style={styles.forecastCard}>
          <Text style={styles.forecastLabel}>12-Month LTV</Text>
          <Text style={styles.forecastValue}>${data?.ltv}</Text>
          <Text style={styles.forecastTrend}>↑ 8% from last month</Text>
        </View>
      </View>

      {/* Churn Risk */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Churn Risk</Text>
        <View style={styles.riskBars}>
          <View style={styles.riskBar}>
            <Text style={styles.riskLabel}>Low Risk</Text>
            <View style={styles.barContainer}>
              <View style={[styles.bar, { width: '78%', backgroundColor: '#2ecc71' }]} />
            </View>
            <Text style={styles.riskPercent}>{data?.churnRisk.low}%</Text>
          </View>
          <View style={styles.riskBar}>
            <Text style={styles.riskLabel}>Medium Risk</Text>
            <View style={styles.barContainer}>
              <View style={[styles.bar, { width: '15%', backgroundColor: '#f39c12' }]} />
            </View>
            <Text style={styles.riskPercent}>{data?.churnRisk.medium}%</Text>
          </View>
          <View style={styles.riskBar}>
            <Text style={styles.riskLabel}>High Risk</Text>
            <View style={styles.barContainer}>
              <View style={[styles.bar, { width: '7%', backgroundColor: '#e74c3c' }]} />
            </View>
            <Text style={styles.riskPercent}>{data?.churnRisk.high}%</Text>
          </View>
        </View>
      </View>

      {/* Segmentation */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Customer Segments</Text>
        {data?.segments.map((segment, index) => (
          <View key={index} style={styles.segmentRow}>
            <View>
              <Text style={styles.segmentName}>{segment.name}</Text>
              <Text style={styles.segmentCount}>{segment.count} customers</Text>
            </View>
            <Text style={[
              styles.segmentGrowth,
              { color: segment.growth.startsWith('+') ? '#2ecc71' : '#e74c3c' }
            ]}>
              {segment.growth}
            </Text>
          </View>
        ))}
      </View>
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
  section: {
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
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metricCard: {
    flex: 1,
    backgroundColor: '#f9f9f9',
    padding: 12,
    borderRadius: 6,
    marginHorizontal: 6,
  },
  metricLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  forecastCard: {
    backgroundColor: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: 20,
    borderRadius: 8,
    alignItems: 'center',
  },
  forecastLabel: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.8)',
    marginBottom: 8,
  },
  forecastValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 8,
  },
  forecastTrend: {
    fontSize: 12,
    color: '#fff',
  },
  riskBars: {
    marginTop: 12,
  },
  riskBar: {
    marginBottom: 16,
  },
  riskLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#333',
    marginBottom: 6,
  },
  barContainer: {
    height: 24,
    backgroundColor: '#f0f0f0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 4,
  },
  bar: {
    height: '100%',
  },
  riskPercent: {
    fontSize: 12,
    color: '#666',
  },
  segmentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  segmentName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  segmentCount: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
  },
  segmentGrowth: {
    fontSize: 14,
    fontWeight: 'bold',
  },
})
