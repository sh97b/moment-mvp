export const mockHealth = {
  status: 'ok',
  service: 'moment-api',
  model_ready: false,
  gemini_available: false,
  mock_fallback_available: true,
}

export const mockScenarios = {
  scenarios: [
    {
      id: 'normal',
      name: '정상 이동',
      description: '평소 경로를 따라 목적지에 다녀옵니다.',
    },
    {
      id: 'temporary_return',
      name: '일시 이탈 후 복귀',
      description: '경로를 잠시 벗어나지만 안내 후 정상 경로로 복귀합니다.',
    },
    {
      id: 'persistent_anomaly',
      name: '이상 이동 지속',
      description: '반복 이동과 방향 전환이 지속되고 집과의 거리가 증가합니다.',
    },
  ],
}

const elderlyAlert = {
  title: '잠시 경로를 확인해 주세요',
  message: '평소 이동 경로와 조금 달라요. 익숙한 길로 돌아가 볼까요?',
}

const levelTwoGuardianAlert = {
  title: '이동 징후를 확인해 주세요',
  message: '평소와 다른 이동 징후가 이어지고 있습니다.',
}

const levelThreeGuardianAlert = {
  title: '보호자 확인이 필요합니다',
  message: '평소와 다른 이동 징후가 계속되어 직접 확인을 권합니다.',
}

export const mockReplays = {
  normal: {
    scenario_id: 'normal',
    interval_ms: 1000,
    frames: [
      {
        timestamp: '2026-08-18T14:00:00+09:00',
        lat: 37.5665,
        lng: 126.978,
        features: { turn_count: 0, revisit_count: 0, home_distance_m: 300, home_distance_delta_m: 12 },
        anomaly_score: 0.08,
        risk_level: 0,
        reasons: [],
        elderly_alert: null,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:01:00+09:00',
        lat: 37.5667,
        lng: 126.9782,
        features: { turn_count: 1, revisit_count: 0, home_distance_m: 315, home_distance_delta_m: 15 },
        anomaly_score: 0.12,
        risk_level: 0,
        reasons: [],
        elderly_alert: null,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:02:00+09:00',
        lat: 37.5669,
        lng: 126.9784,
        features: { turn_count: 1, revisit_count: 0, home_distance_m: 308, home_distance_delta_m: -7 },
        anomaly_score: 0.1,
        risk_level: 0,
        reasons: [],
        elderly_alert: null,
        guardian_alert: null,
      },
    ],
  },
  temporary_return: {
    scenario_id: 'temporary_return',
    interval_ms: 1000,
    frames: [
      {
        timestamp: '2026-08-18T14:00:00+09:00',
        lat: 37.5665,
        lng: 126.978,
        features: { turn_count: 1, revisit_count: 0, home_distance_m: 320, home_distance_delta_m: 10 },
        anomaly_score: 0.12,
        risk_level: 0,
        reasons: [],
        elderly_alert: null,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:01:00+09:00',
        lat: 37.5672,
        lng: 126.9792,
        features: { turn_count: 2, revisit_count: 0, home_distance_m: 370, home_distance_delta_m: 50 },
        anomaly_score: 0.7,
        risk_level: 1,
        reasons: [
          '평소 이동 경로에서 벗어난 상태가 감지되었습니다.',
          '이동 패턴의 이상 점수가 기준을 넘었습니다.',
        ],
        elderly_alert: elderlyAlert,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:02:00+09:00',
        lat: 37.5669,
        lng: 126.9786,
        features: { turn_count: 1, revisit_count: 0, home_distance_m: 345, home_distance_delta_m: -25 },
        anomaly_score: 0.2,
        risk_level: 1,
        reasons: ['평소 경로로 복귀하는 흐름이 확인되었습니다.'],
        elderly_alert: elderlyAlert,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:03:00+09:00',
        lat: 37.5666,
        lng: 126.9781,
        features: { turn_count: 0, revisit_count: 0, home_distance_m: 315, home_distance_delta_m: -30 },
        anomaly_score: 0.1,
        risk_level: 0,
        reasons: ['평소 경로로 복귀하는 흐름이 확인되었습니다.'],
        elderly_alert: null,
        guardian_alert: null,
      },
    ],
  },
  persistent_anomaly: {
    scenario_id: 'persistent_anomaly',
    interval_ms: 1000,
    frames: [
      {
        timestamp: '2026-08-18T14:00:00+09:00',
        lat: 37.5665,
        lng: 126.978,
        features: { turn_count: 1, revisit_count: 0, home_distance_m: 300, home_distance_delta_m: 10 },
        anomaly_score: 0.1,
        risk_level: 0,
        reasons: [],
        elderly_alert: null,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:01:00+09:00',
        lat: 37.5674,
        lng: 126.9794,
        features: { turn_count: 2, revisit_count: 0, home_distance_m: 380, home_distance_delta_m: 80 },
        anomaly_score: 0.7,
        risk_level: 1,
        reasons: [
          '평소 이동 경로에서 벗어난 상태가 감지되었습니다.',
          '이동 패턴의 이상 점수가 기준을 넘었습니다.',
        ],
        elderly_alert: elderlyAlert,
        guardian_alert: null,
      },
      {
        timestamp: '2026-08-18T14:02:00+09:00',
        lat: 37.5681,
        lng: 126.9801,
        features: { turn_count: 5, revisit_count: 1, home_distance_m: 470, home_distance_delta_m: 90 },
        anomaly_score: 0.82,
        risk_level: 2,
        reasons: [
          '평소 이동 경로에서 벗어난 상태가 감지되었습니다.',
          '한 구간에 머문 시간이 평소보다 깁니다.',
          '최근 구간의 방향 전환이 평소보다 많습니다.',
          '이동 패턴의 이상 점수가 기준을 넘었습니다.',
        ],
        elderly_alert: elderlyAlert,
        guardian_alert: levelTwoGuardianAlert,
      },
      {
        timestamp: '2026-08-18T14:03:00+09:00',
        lat: 37.5688,
        lng: 126.9808,
        features: { turn_count: 7, revisit_count: 3, home_distance_m: 580, home_distance_delta_m: 110 },
        anomaly_score: 0.92,
        risk_level: 3,
        reasons: [
          '평소 이동 경로에서 벗어난 상태가 감지되었습니다.',
          '한 구간에 머문 시간이 평소보다 깁니다.',
          '최근 구간의 방향 전환이 평소보다 많습니다.',
          '같은 구간을 반복해서 이동하는 징후가 있습니다.',
          '이동 패턴의 이상 점수가 기준을 넘었습니다.',
        ],
        elderly_alert: elderlyAlert,
        guardian_alert: levelThreeGuardianAlert,
      },
    ],
  },
}
