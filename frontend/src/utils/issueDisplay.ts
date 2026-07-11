type IssueDisplayInput = {
  id: string;
  title: string;
  description?: string;
  category: string;
};

export type IssueDisplayCopy = {
  displayTitle: string;
  displaySubtitle: string;
  topicLabel: string;
  resolutionCondition: string;
  sourceTitle: string;
};

type IssueDisplayOverride = Omit<IssueDisplayCopy, "sourceTitle">;

const OVERRIDES_BY_TITLE: Record<string, IssueDisplayOverride> = {
  "will hamas agree to disarm by december 31?": {
    displayTitle: "가자 휴전 조건 이슈",
    displaySubtitle: "12월 31일까지 하마스의 무장 해제 합의 여부를 다룹니다.",
    topicLabel: "가자 분쟁",
    resolutionCondition: "기준일까지 하마스가 무장 해제에 합의하는지 여부",
  },
  "will abstract launch a token by december 31, 2027?": {
    displayTitle: "Abstract 토큰 출시 이슈",
    displaySubtitle:
      "2027년 12월 31일까지 Abstract의 토큰 출시 여부를 다룹니다.",
    topicLabel: "가상자산 인프라",
    resolutionCondition: "기준일까지 Abstract 토큰 출시가 확인되는지 여부",
  },
  "will russia capture kostyantynivka by september 30?": {
    displayTitle: "코스티안티니우카 전황 변화 이슈",
    displaySubtitle:
      "9월 30일까지 러시아의 코스티안티니우카 장악 여부를 다룹니다.",
    topicLabel: "우크라이나 전쟁",
    resolutionCondition:
      "기준일까지 러시아의 코스티안티니우카 장악이 확인되는지 여부",
  },
  "israeli parliament dissolved by july 31?": {
    displayTitle: "이스라엘 의회 해산 이슈",
    displaySubtitle: "7월 31일까지 이스라엘 의회 해산 여부를 다룹니다.",
    topicLabel: "이스라엘 정치",
    resolutionCondition: "기준일까지 이스라엘 의회 해산이 확인되는지 여부",
  },
  "will any presidential candidate win outright in the first round of the brazil election?":
    {
      displayTitle: "브라질 대선 1차 투표 이슈",
      displaySubtitle:
        "브라질 대선 1차 투표에서 결선 없이 당선자가 정해지는지 다룹니다.",
      topicLabel: "브라질 정치",
      resolutionCondition:
        "브라질 대선 1차 투표에서 과반 득표자가 나오는지 여부",
    },
  "putin out as president of russia by december 31, 2026?": {
    displayTitle: "러시아 대통령직 변화 이슈",
    displaySubtitle: "2026년 12월 31일까지 푸틴 대통령직 변화 여부를 다룹니다.",
    topicLabel: "러시아 정치",
    resolutionCondition:
      "기준일까지 푸틴이 러시아 대통령직에서 물러나는지 여부",
  },
  "will the democratic party control the senate after the 2026 midterm elections?":
    {
      displayTitle: "미국 상원 다수당 이슈",
      displaySubtitle:
        "2026년 중간선거 이후 민주당의 상원 다수당 여부를 다룹니다.",
      topicLabel: "미국 의회",
      resolutionCondition:
        "2026년 중간선거 이후 민주당이 상원을 장악하는지 여부",
    },
  "macron out by july 31, 2026?": {
    displayTitle: "프랑스 대통령직 변화 이슈",
    displaySubtitle:
      "2026년 7월 31일까지 프랑스 대통령의 재임 상태 변화를 다룹니다.",
    topicLabel: "프랑스 정치",
    resolutionCondition: "기준일까지 프랑스 대통령의 재임 상태가 바뀌는지 여부",
  },
  "xi jinping out before 2027?": {
    displayTitle: "중국 지도부 변화 이슈",
    displaySubtitle: "2027년 전까지 시진핑의 지도자 지위 변화 여부를 다룹니다.",
    topicLabel: "중국 정치",
    resolutionCondition:
      "기준일까지 시진핑의 지도자 지위 변화가 확인되는지 여부",
  },
  "will trump be impeached by end of 2026?": {
    displayTitle: "트럼프 탄핵 절차 이슈",
    displaySubtitle: "2026년 말까지 트럼프 탄핵 절차 진행 여부를 다룹니다.",
    topicLabel: "미국 정치",
    resolutionCondition: "기준일까지 트럼프 탄핵이 확인되는지 여부",
  },
  "will gpt-6 be released by july 31, 2026?": {
    displayTitle: "GPT-6 공개 일정 이슈",
    displaySubtitle: "2026년 7월 31일까지 GPT-6 공개 여부를 다룹니다.",
    topicLabel: "AI 기술",
    resolutionCondition: "기준일까지 GPT-6 공개가 확인되는지 여부",
  },
  "will china invade taiwan by end of 2026?": {
    displayTitle: "대만해협 군사 긴장 이슈",
    displaySubtitle: "2026년 말까지 중국의 대만 침공 여부를 다룹니다.",
    topicLabel: "동아시아 안보",
    resolutionCondition: "기준일까지 중국의 대만 침공이 확인되는지 여부",
  },
  "will spain win the 2026 fifa world cup?": {
    displayTitle: "스페인 월드컵 결과 이슈",
    displaySubtitle:
      "2026년 FIFA 월드컵에서 스페인의 최종 우승 여부를 다룹니다.",
    topicLabel: "스포츠",
    resolutionCondition: "2026년 FIFA 월드컵에서 스페인이 우승하는지 여부",
  },
  "netanyahu out by july 31?": {
    displayTitle: "이스라엘 총리직 변화 이슈",
    displaySubtitle: "7월 31일까지 네타냐후 총리직 변화 여부를 다룹니다.",
    topicLabel: "이스라엘 정치",
    resolutionCondition: "기준일까지 네타냐후가 총리직에서 물러나는지 여부",
  },
  "will jd vance win the 2028 us presidential election?": {
    displayTitle: "2028년 미국 대선 결과 이슈",
    displaySubtitle: "2028년 미국 대선에서 JD 밴스 당선 여부를 다룹니다.",
    topicLabel: "미국 대선",
    resolutionCondition: "2028년 미국 대선에서 JD 밴스 당선이 확인되는지 여부",
  },
  "will ostium launch a token by december 31, 2026?": {
    displayTitle: "Ostium 토큰 출시 이슈",
    displaySubtitle: "2026년 12월 31일까지 Ostium의 토큰 출시 여부를 다룹니다.",
    topicLabel: "가상자산 인프라",
    resolutionCondition: "기준일까지 Ostium 토큰 출시가 확인되는지 여부",
  },
  "will bitcoin hit $150k by december 31, 2026?": {
    displayTitle: "비트코인 가격 기준선 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 비트코인이 15만 달러 기준선에 도달하는지 다룹니다.",
    topicLabel: "가상자산",
    resolutionCondition:
      "기준일까지 비트코인이 15만 달러 기준선에 도달하는지 여부",
  },
  "will any country leave nato by december 31, 2026?": {
    displayTitle: "NATO 회원국 이탈 이슈",
    displaySubtitle: "2026년 12월 31일까지 NATO 회원국 이탈 여부를 다룹니다.",
    topicLabel: "국제 안보",
    resolutionCondition: "기준일까지 한 국가 이상이 NATO를 탈퇴하는지 여부",
  },
  "will gavin newsom win the 2028 democratic presidential nomination?": {
    displayTitle: "2028년 미국 민주당 대선 후보 이슈",
    displaySubtitle:
      "2028년 미국 대선에서 개빈 뉴섬의 민주당 후보 지명 여부를 다룹니다.",
    topicLabel: "미국 대선",
    resolutionCondition:
      "2028년 미국 민주당 대선 후보로 개빈 뉴섬이 지명되는지 여부",
  },
  "will donald trump win the 2028 republican presidential nomination?": {
    displayTitle: "2028년 미국 공화당 대선 후보 이슈",
    displaySubtitle:
      "2028년 미국 대선에서 도널드 트럼프의 공화당 후보 지명 여부를 다룹니다.",
    topicLabel: "미국 대선",
    resolutionCondition:
      "2028년 미국 공화당 대선 후보로 도널드 트럼프가 지명되는지 여부",
  },
  "will the republicans win the 2028 us presidential election?": {
    displayTitle: "2028년 미국 대선 정당 결과 이슈",
    displaySubtitle: "2028년 미국 대선에서 공화당 후보 당선 여부를 다룹니다.",
    topicLabel: "미국 대선",
    resolutionCondition:
      "2028년 미국 대선에서 공화당 후보 당선이 확인되는지 여부",
  },
  "zelenskyy out as ukraine president by end of 2026?": {
    displayTitle: "우크라이나 대통령직 변화 이슈",
    displaySubtitle: "2026년 말까지 젤렌스키 대통령직 변화 여부를 다룹니다.",
    topicLabel: "우크라이나 정치",
    resolutionCondition: "기준일까지 젤렌스키가 대통령직에서 물러나는지 여부",
  },
  "2026 balance of power: d senate, d house": {
    displayTitle: "2026년 미국 의회 권력 균형 이슈",
    displaySubtitle:
      "2026년 선거 이후 민주당의 상원·하원 동시 다수당 여부를 다룹니다.",
    topicLabel: "미국 의회",
    resolutionCondition:
      "2026년 이후 민주당이 상원과 하원을 모두 장악하는지 여부",
  },
  "will tarcisio de freitas win the 2026 brazilian presidential election?": {
    displayTitle: "2026년 브라질 대선 결과 이슈",
    displaySubtitle:
      "2026년 브라질 대선에서 타르시지우 지 프레이타스 당선 여부를 다룹니다.",
    topicLabel: "브라질 정치",
    resolutionCondition:
      "2026년 브라질 대선에서 타르시지우 지 프레이타스 당선이 확인되는지 여부",
  },
  "will the democratic party control the house after the 2026 midterm elections?":
    {
      displayTitle: "미국 하원 다수당 이슈",
      displaySubtitle:
        "2026년 중간선거 이후 민주당의 하원 다수당 여부를 다룹니다.",
      topicLabel: "미국 의회",
      resolutionCondition:
        "2026년 중간선거 이후 민주당이 하원을 장악하는지 여부",
    },
  "will mallory mcmorrow win the 2026 michigan democratic primary?": {
    displayTitle: "미시간 민주당 예비선거 이슈",
    displaySubtitle:
      "2026년 미시간 민주당 예비선거에서 맬러리 맥모로 후보 결과를 다룹니다.",
    topicLabel: "미국 선거",
    resolutionCondition:
      "2026년 미시간 민주당 예비선거에서 맬러리 맥모로가 승리하는지 여부",
  },
  "erdoğan out by december 31, 2026?": {
    displayTitle: "튀르키예 대통령직 변화 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 에르도안 대통령직 변화 여부를 다룹니다.",
    topicLabel: "튀르키예 정치",
    resolutionCondition: "기준일까지 에르도안이 대통령직에서 물러나는지 여부",
  },
  "will trump pardon ghislaine maxwell by end of 2026?": {
    displayTitle: "트럼프 사면 결정 이슈",
    displaySubtitle:
      "2026년 말까지 트럼프의 기슬레인 맥스웰 사면 여부를 다룹니다.",
    topicLabel: "미국 정치",
    resolutionCondition:
      "기준일까지 트럼프의 기슬레인 맥스웰 사면이 확인되는지 여부",
  },
  "will openai launch a new consumer hardware product by december 31, 2026?": {
    displayTitle: "OpenAI 소비자 하드웨어 출시 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 OpenAI의 소비자용 하드웨어 출시 여부를 다룹니다.",
    topicLabel: "AI 기술",
    resolutionCondition:
      "기준일까지 OpenAI의 소비자용 하드웨어 출시가 확인되는지 여부",
  },
  "will bernie endorse james talarico for tx-sen by nov 2 2026 et?": {
    displayTitle: "텍사스 상원 선거 지지 선언 이슈",
    displaySubtitle:
      "2026년 11월 2일까지 버니 샌더스의 제임스 탈라리코 지지 선언 여부를 다룹니다.",
    topicLabel: "미국 선거",
    resolutionCondition:
      "기준일까지 버니 샌더스의 제임스 탈라리코 지지 선언이 확인되는지 여부",
  },
  "scotus accepts sports event contract case by july 31, 2026?": {
    displayTitle: "미국 연방대법원 사건 접수 이슈",
    displaySubtitle:
      "2026년 7월 31일까지 스포츠 이벤트 계약 관련 사건 접수 여부를 다룹니다.",
    topicLabel: "미국 사법",
    resolutionCondition: "기준일까지 연방대법원의 사건 접수가 확인되는지 여부",
  },
  "ukraine election called by december 31, 2026?": {
    displayTitle: "우크라이나 선거 공고 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 우크라이나 선거 공고 여부를 다룹니다.",
    topicLabel: "우크라이나 정치",
    resolutionCondition: "기준일까지 우크라이나 선거 공고가 확인되는지 여부",
  },
  "will russia capture lyman by september 30, 2026?": {
    displayTitle: "리만 전황 변화 이슈",
    displaySubtitle: "2026년 9월 30일까지 러시아의 리만 장악 여부를 다룹니다.",
    topicLabel: "우크라이나 전쟁",
    resolutionCondition: "기준일까지 러시아의 리만 장악이 확인되는지 여부",
  },
  "will openai not ipo by december 31, 2026?": {
    displayTitle: "OpenAI 상장 일정 이슈",
    displaySubtitle: "2026년 12월 31일까지 OpenAI의 상장 여부를 다룹니다.",
    topicLabel: "AI 산업",
    resolutionCondition: "기준일까지 OpenAI 상장이 확인되는지 여부",
  },
  "will pump.fun perform an airdrop by december 31, 2026": {
    displayTitle: "Pump.fun 에어드롭 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 Pump.fun의 에어드롭 진행 여부를 다룹니다.",
    topicLabel: "가상자산",
    resolutionCondition: "기준일까지 Pump.fun 에어드롭이 확인되는지 여부",
  },
  "spain snap election called by august 31, 2026?": {
    displayTitle: "스페인 조기총선 이슈",
    displaySubtitle:
      "2026년 8월 31일까지 스페인 조기총선 공고 여부를 다룹니다.",
    topicLabel: "스페인 정치",
    resolutionCondition: "기준일까지 스페인 조기총선 공고가 확인되는지 여부",
  },
  "kraken ipo by december 31, 2026?": {
    displayTitle: "Kraken 상장 일정 이슈",
    displaySubtitle: "2026년 12월 31일까지 Kraken의 상장 여부를 다룹니다.",
    topicLabel: "가상자산 산업",
    resolutionCondition: "기준일까지 Kraken 상장이 확인되는지 여부",
  },
  "will the next uk election be called by december 31, 2026?": {
    displayTitle: "영국 차기 총선 공고 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 영국 차기 총선 공고 여부를 다룹니다.",
    topicLabel: "영국 정치",
    resolutionCondition: "기준일까지 영국 차기 총선 공고가 확인되는지 여부",
  },
  "will base launch a token by june 30, 2027?": {
    displayTitle: "Base 토큰 출시 이슈",
    displaySubtitle: "2027년 6월 30일까지 Base의 토큰 출시 여부를 다룹니다.",
    topicLabel: "가상자산 인프라",
    resolutionCondition: "기준일까지 Base 토큰 출시가 확인되는지 여부",
  },
  "will unit launch a token by december 31, 2026?": {
    displayTitle: "Unit 토큰 출시 이슈",
    displaySubtitle: "2026년 12월 31일까지 Unit의 토큰 출시 여부를 다룹니다.",
    topicLabel: "가상자산 인프라",
    resolutionCondition: "기준일까지 Unit 토큰 출시가 확인되는지 여부",
  },
  "will russia capture sumy by march 31, 2027?": {
    displayTitle: "수미 전황 변화 이슈",
    displaySubtitle: "2027년 3월 31일까지 러시아의 수미 장악 여부를 다룹니다.",
    topicLabel: "우크라이나 전쟁",
    resolutionCondition: "기준일까지 러시아의 수미 장악이 확인되는지 여부",
  },
  "china x india military clash by december 31, 2026?": {
    displayTitle: "중국·인도 군사 충돌 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 중국과 인도 간 군사 충돌 여부를 다룹니다.",
    topicLabel: "아시아 안보",
    resolutionCondition:
      "기준일까지 중국과 인도 간 군사 충돌이 확인되는지 여부",
  },
  "u.s. x russia nuclear deal by december 31, 2026?": {
    displayTitle: "미국·러시아 핵 합의 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 미국과 러시아의 핵 관련 합의 여부를 다룹니다.",
    topicLabel: "국제 안보",
    resolutionCondition:
      "기준일까지 미국과 러시아의 핵 관련 합의가 확인되는지 여부",
  },
  "will metamask launch a token by september 30, 2026?": {
    displayTitle: "MetaMask 토큰 출시 이슈",
    displaySubtitle:
      "2026년 9월 30일까지 MetaMask의 토큰 출시 여부를 다룹니다.",
    topicLabel: "가상자산 인프라",
    resolutionCondition: "기준일까지 MetaMask 토큰 출시가 확인되는지 여부",
  },
  "ukraine election held by december 31, 2026?": {
    displayTitle: "우크라이나 선거 실시 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 우크라이나 선거 실시 여부를 다룹니다.",
    topicLabel: "우크라이나 정치",
    resolutionCondition: "기준일까지 우크라이나 선거 실시가 확인되는지 여부",
  },
  "will trump resign by december 31, 2026?": {
    displayTitle: "미국 대통령직 변화 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 트럼프 대통령직 변화 여부를 다룹니다.",
    topicLabel: "미국 정치",
    resolutionCondition: "기준일까지 트럼프가 대통령직에서 물러나는지 여부",
  },
  "ukraine recognizes russian sovereignty over its territory by december 31, 2026?":
    {
      displayTitle: "우크라이나 영토 승인 이슈",
      displaySubtitle:
        "2026년 12월 31일까지 우크라이나의 러시아 영유권 인정 여부를 다룹니다.",
      topicLabel: "우크라이나 전쟁",
      resolutionCondition:
        "기준일까지 우크라이나의 러시아 영유권 인정이 확인되는지 여부",
    },
  "will tarcisio de frietas qualify for brazil's presidential runoff?": {
    displayTitle: "브라질 대선 결선 진출 이슈",
    displaySubtitle:
      "타르시지우 지 프레이타스의 브라질 대선 결선 진출 여부를 다룹니다.",
    topicLabel: "브라질 정치",
    resolutionCondition:
      "브라질 대선에서 타르시지우 지 프레이타스의 결선 진출이 확인되는지 여부",
  },
  "will megaeth perform an airdrop by december 31, 2026?": {
    displayTitle: "MegaETH 에어드롭 이슈",
    displaySubtitle:
      "2026년 12월 31일까지 MegaETH의 에어드롭 진행 여부를 다룹니다.",
    topicLabel: "가상자산",
    resolutionCondition: "기준일까지 MegaETH 에어드롭이 확인되는지 여부",
  },
  "will axiom launch a token by december 31, 2026?": {
    displayTitle: "Axiom 토큰 출시 이슈",
    displaySubtitle: "2026년 12월 31일까지 Axiom의 토큰 출시 여부를 다룹니다.",
    topicLabel: "가상자산 인프라",
    resolutionCondition: "기준일까지 Axiom 토큰 출시가 확인되는지 여부",
  },
};

function normalizeTitle(title: string): string {
  return title.trim().replace(/\s+/g, " ").toLowerCase();
}

function fallbackTopicLabel(category: string, title = ""): string {
  const normalized = `${title} ${category}`.trim().toLowerCase();
  if (normalized.includes("iran")) return "이란 전쟁";
  if (normalized.includes("ukraine")) return "우크라이나 이슈";
  if (normalized.includes("gaza")) return "가자 분쟁";
  if (normalized.includes("crypto") || normalized.includes("token"))
    return "가상자산";
  if (normalized.includes("politics") || normalized.includes("president"))
    return "정치";
  if (normalized.includes("geopolitics")) return "국제 정세";
  if (normalized.includes("tech") || normalized.includes("openai"))
    return "기술";
  if (normalized.includes("sports")) return "스포츠";
  return category || "이슈";
}

function fallbackDisplayTitle(title: string, category: string): string {
  const cleanTitle = title.trim().replace(/\?+$/, "");
  const normalized = normalizeTitle(title);
  const topicLabel = fallbackTopicLabel(category, title);

  if (/[ㄱ-ㅎㅏ-ㅣ가-힣]/.test(cleanTitle)) {
    return cleanTitle;
  }

  if (normalized.includes("launch a token")) return "토큰 출시 이슈";
  if (normalized.includes("airdrop")) return "에어드롭 이슈";
  if (normalized.includes("ipo")) return "상장 일정 이슈";
  if (normalized.includes("iran")) return "이란 전쟁 이슈";
  if (normalized.includes("election")) return "선거 일정·결과 이슈";
  if (normalized.includes("out") || normalized.includes("resign")) {
    return "정치 리더십 변화 이슈";
  }
  if (normalized.includes("capture")) return "전황 변화 이슈";

  return `${topicLabel} 변화 이슈`;
}

export function buildIssueDisplayCopy(
  input: IssueDisplayInput,
): IssueDisplayCopy {
  const sourceTitle = input.title.trim();
  const override = OVERRIDES_BY_TITLE[normalizeTitle(sourceTitle)];
  if (override) {
    return { ...override, sourceTitle };
  }

  const displayTitle = fallbackDisplayTitle(sourceTitle, input.category);
  const topicLabel = fallbackTopicLabel(input.category, sourceTitle);
  const resolutionCondition = input.description?.trim() || sourceTitle;

  return {
    sourceTitle,
    displayTitle,
    displaySubtitle: "등록된 시장 질문의 기준 조건을 다룹니다.",
    topicLabel,
    resolutionCondition,
  };
}
