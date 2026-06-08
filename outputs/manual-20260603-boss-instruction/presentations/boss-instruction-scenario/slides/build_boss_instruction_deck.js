const pptxgen = require("/Users/amadey/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs");

const pptx = new pptxgen();
pptx.layout = "LAYOUT_WIDE";
pptx.author = "Ouroboros";
pptx.subject = "Сценарий агента по поручениям руководства";
pptx.title = "Ouroboros: агентный разбор поручений руководства";
pptx.company = "Ouroboros";
pptx.lang = "ru-RU";
pptx.theme = {
  headFontFace: "Aptos Display",
  bodyFontFace: "Aptos",
  lang: "ru-RU",
};
pptx.defineLayout({ name: "CUSTOM_WIDE", width: 13.333, height: 7.5 });
pptx.layout = "CUSTOM_WIDE";
pptx.margin = 0;

const C = {
  navy: "0B2545",
  ink: "162033",
  slate: "4C5A6A",
  pale: "F6F8FB",
  line: "D9E1EC",
  blue: "2E74B5",
  cyan: "4AA3DF",
  green: "2E8B57",
  amber: "D48A17",
  red: "B85042",
  violet: "6E56CF",
  white: "FFFFFF",
};

function addFooter(slide, n) {
  slide.addText("Ouroboros для руководителя банка", {
    x: 0.42, y: 7.12, w: 4.1, h: 0.18,
    fontFace: "Aptos", fontSize: 7.5, color: "7B8794",
    margin: 0,
  });
  slide.addText(String(n).padStart(2, "0"), {
    x: 12.45, y: 7.08, w: 0.45, h: 0.2,
    fontFace: "Aptos", fontSize: 8, bold: true, color: "7B8794",
    align: "right", margin: 0,
  });
}

function title(slide, eyebrow, heading, sub, n) {
  slide.background = { color: C.pale };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.11, fill: { color: C.blue }, line: { color: C.blue } });
  slide.addText(eyebrow.toUpperCase(), {
    x: 0.62, y: 0.42, w: 4.7, h: 0.22,
    fontFace: "Aptos", fontSize: 8.5, bold: true, color: C.blue,
    charSpace: 0.5, margin: 0,
  });
  slide.addText(heading, {
    x: 0.6, y: 0.76, w: 8.9, h: 0.86,
    fontFace: "Aptos Display", fontSize: 27, bold: true, color: C.navy,
    breakLine: false, fit: "shrink", margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: 0.62, y: 1.66, w: 8.25, h: 0.42,
      fontFace: "Aptos", fontSize: 10.5, color: C.slate,
      fit: "shrink", margin: 0,
    });
  }
  addFooter(slide, n);
}

function pill(slide, text, x, y, w, color, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h: opts.h || 0.34,
    rectRadius: 0.06,
    fill: { color: opts.fill || C.white },
    line: { color, width: 1 },
  });
  slide.addText(text, {
    x: x + 0.08, y: y + 0.08, w: w - 0.16, h: 0.12,
    fontFace: "Aptos", fontSize: opts.fontSize || 7.7, bold: true,
    color, align: "center", fit: "shrink", margin: 0,
  });
}

function card(slide, x, y, w, h, heading, body, color = C.blue, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h,
    rectRadius: 0.05,
    fill: { color: opts.fill || C.white },
    line: { color: opts.line || C.line, width: 1 },
  });
  slide.addShape(pptx.ShapeType.rect, { x, y, w: 0.08, h, fill: { color }, line: { color } });
  slide.addText(heading, {
    x: x + 0.22, y: y + 0.18, w: w - 0.42, h: 0.23,
    fontFace: "Aptos", fontSize: opts.headingSize || 11, bold: true, color: C.navy,
    fit: "shrink", margin: 0,
  });
  slide.addText(body, {
    x: x + 0.22, y: y + 0.55, w: w - 0.42, h: h - 0.74,
    fontFace: "Aptos", fontSize: opts.bodySize || 8.5, color: opts.bodyColor || C.slate,
    fit: "shrink", valign: "top", breakLine: false, margin: 0,
  });
}

function arrow(slide, x1, y1, x2, y2, color = C.blue) {
  slide.addShape(pptx.ShapeType.line, {
    x: x1, y: y1, w: x2 - x1, h: y2 - y1,
    line: { color, width: 1.4, beginArrowType: "none", endArrowType: "triangle" },
  });
}

function smallLabel(slide, text, x, y, w, color = C.slate) {
  slide.addText(text, {
    x, y, w, h: 0.22,
    fontFace: "Aptos", fontSize: 7.5, bold: true, color,
    fit: "shrink", margin: 0,
  });
}

function agendaRow(slide, n, label, value, x, y, color) {
  slide.addShape(pptx.ShapeType.ellipse, {
    x, y: y + 0.03, w: 0.36, h: 0.36,
    fill: { color }, line: { color },
  });
  slide.addText(String(n), {
    x: x + 0.115, y: y + 0.125, w: 0.13, h: 0.08,
    fontFace: "Aptos", fontSize: 8, bold: true, color: C.white, margin: 0,
  });
  slide.addText(label, {
    x: x + 0.52, y, w: 2.4, h: 0.22,
    fontFace: "Aptos", fontSize: 10.5, bold: true, color: C.navy, margin: 0,
  });
  slide.addText(value, {
    x: x + 0.52, y: y + 0.32, w: 4.15, h: 0.42,
    fontFace: "Aptos", fontSize: 8.6, color: C.slate, fit: "shrink", margin: 0,
  });
}

// 1
{
  const slide = pptx.addSlide();
  slide.background = { color: C.navy };
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 5.7, h: 7.5, fill: { color: "102F54", transparency: 8 }, line: { color: "102F54" } });
  slide.addText("OUROBOROS", { x: 0.62, y: 0.55, w: 2, h: 0.18, fontFace: "Aptos", fontSize: 8.5, bold: true, color: C.cyan, charSpace: 1, margin: 0 });
  slide.addText("Агентный разбор поручений руководства", {
    x: 0.62, y: 1.22, w: 7.25, h: 1.35,
    fontFace: "Aptos Display", fontSize: 34, bold: true, color: C.white,
    fit: "shrink", margin: 0,
  });
  slide.addText("Сценарий демонстрирует другую возможность агента: из поручения руководителя автоматически выделить тип работы, ответственных, источники, риски, срок и формат управленческого результата.", {
    x: 0.65, y: 2.9, w: 5.9, h: 0.7,
    fontFace: "Aptos", fontSize: 12.2, color: "D5DEE9",
    fit: "shrink", margin: 0,
  });
  const cats = ["Аналитика", "Финансы", "Пилоты", "Риски", "Технологии", "Встречи", "ДЗО / Сеть", "Иное"];
  cats.forEach((c, i) => pill(slide, c, 7.6 + (i % 2) * 2.25, 1.25 + Math.floor(i / 2) * 0.72, 1.85, [C.cyan, C.amber, C.green, C.red][i % 4], { fill: "123B67" }));
  slide.addShape(pptx.ShapeType.roundRect, {
    x: 7.55, y: 4.65, w: 4.6, h: 1.1,
    rectRadius: 0.05,
    fill: { color: "0F355E" },
    line: { color: "2F5B86", width: 1 },
  });
  slide.addText("Основа: классификатор из проекта anton/reports", {
    x: 7.85, y: 4.92, w: 4.0, h: 0.22,
    fontFace: "Aptos", fontSize: 10.5, bold: true, color: C.white, margin: 0,
  });
  slide.addText("multi-label разметка поручений + debug-трассировка правил", {
    x: 7.85, y: 5.26, w: 4.0, h: 0.2,
    fontFace: "Aptos", fontSize: 8.7, color: "C9D7E6", margin: 0,
  });
}

// 2
{
  const slide = pptx.addSlide();
  title(slide, "Зачем сценарий", "Проблема не в классификации, а в потере управляемости поручений", "Поручение руководителя часто содержит несколько типов работы сразу: встречу, аналитику, финансы, риски, технологический контур и внешние запросы.", 2);
  card(slide, 0.7, 2.45, 2.75, 2.2, "Вход", "Свободный текст поручения, краткое содержание, срок, автор, адресаты, вложения и статус исполнения.", C.blue);
  arrow(slide, 3.68, 3.55, 4.55, 3.55);
  card(slide, 4.75, 2.45, 3.5, 2.2, "Агентная обработка", "Нормализует формулировку, ставит категории, проверяет неоднозначности, собирает источники и предлагает маршрут исполнения.", C.green);
  arrow(slide, 8.48, 3.55, 9.34, 3.55);
  card(slide, 9.55, 2.45, 2.95, 2.2, "Выход", "Размеченный отчет, краткий briefing, список владельцев, риски, вопросы на уточнение и audit trail.", C.amber);
  slide.addText("Ключевой тезис", { x: 0.72, y: 5.38, w: 1.5, h: 0.18, fontFace: "Aptos", fontSize: 8.3, bold: true, color: C.blue, margin: 0 });
  slide.addText("Агент не заменяет руководителя или исполнителя: он превращает неструктурированное поручение в управляемый объект с категорией, статусом, источниками и следующими действиями.", {
    x: 0.72, y: 5.72, w: 11.2, h: 0.46,
    fontFace: "Aptos Display", fontSize: 16.2, bold: true, color: C.navy,
    fit: "shrink", margin: 0,
  });
}

// 3
{
  const slide = pptx.addSlide();
  title(slide, "Когда запускать", "Триггеры сценария наследуют рамку срочной подготовки к встречам", "Нужен явный управленческий контекст, а не просто поиск по документам.", 3);
  card(slide, 0.75, 2.22, 3.65, 2.85, "Запускать", "• есть поручение или пункт отчета руководства\n• нужно разнести по категориям\n• требуется подготовить справку, маршрут или статус\n• есть срок, ответственный или управленческий адресат", C.green, { bodySize: 8.9 });
  card(slide, 4.85, 2.22, 3.65, 2.85, "Сначала уточнить", "• непонятен объект поручения\n• нет срока или ожидаемого результата\n• пересекаются несколько владельцев\n• категория влияет на доступ к закрытым данным", C.amber, { bodySize: 8.9 });
  card(slide, 8.95, 2.22, 3.65, 2.85, "Не запускать", "• запрос про финальное решение вместо ответственного\n• попытка обойти полномочия или согласование\n• нет управленческого поручения\n• нужен публичный текст без внутреннего workflow", C.red, { bodySize: 8.9 });
  slide.addShape(pptx.ShapeType.roundRect, { x: 1.05, y: 5.62, w: 11.2, h: 0.72, rectRadius: 0.04, fill: { color: "EAF2FB" }, line: { color: "BFD5EA" } });
  slide.addText("Правило запуска: если в запросе есть объект поручения, ожидаемый управленческий результат и необходимость разметки/маршрутизации, агент начинает обработку. Если один признак отсутствует, задается короткий уточняющий вопрос.", {
    x: 1.25, y: 5.86, w: 10.8, h: 0.18,
    fontFace: "Aptos", fontSize: 9.3, bold: true, color: C.navy,
    fit: "shrink", margin: 0,
  });
}

// 4
{
  const slide = pptx.addSlide();
  title(slide, "Как работает", "Workflow агента: от текста поручения к управленческому артефакту", "Классификация - первый слой. Ценность появляется после проверки, обогащения и фиксации next steps.", 4);
  const steps = [
    ["1", "Принять поручение", "текст, срок, автор, адресаты"],
    ["2", "Нормализовать", "колонки, пробелы, регистр, ё/е"],
    ["3", "Классифицировать", "multi-label категории + Иное"],
    ["4", "Обогатить", "источники, прошлые поручения, документы"],
    ["5", "Собрать briefing", "суть, статус, риски, вопросы"],
    ["6", "Зафиксировать аудит", "правила, источники, ограничения"],
  ];
  steps.forEach((s, i) => {
    const x = 0.58 + i * 2.08;
    slide.addShape(pptx.ShapeType.ellipse, { x, y: 2.28, w: 0.54, h: 0.54, fill: { color: [C.blue, C.cyan, C.green, C.amber, C.violet, C.red][i] }, line: { color: [C.blue, C.cyan, C.green, C.amber, C.violet, C.red][i] } });
    slide.addText(s[0], { x: x + 0.21, y: 2.46, w: 0.1, h: 0.08, fontFace: "Aptos", fontSize: 8, bold: true, color: C.white, margin: 0 });
    if (i < steps.length - 1) arrow(slide, x + 0.68, 2.55, x + 1.72, 2.55, "9CB5CC");
    slide.addText(s[1], { x: x - 0.05, y: 3.08, w: 1.3, h: 0.3, fontFace: "Aptos", fontSize: 9.2, bold: true, color: C.navy, align: "center", fit: "shrink", margin: 0 });
    slide.addText(s[2], { x: x - 0.18, y: 3.52, w: 1.55, h: 0.38, fontFace: "Aptos", fontSize: 7.5, color: C.slate, align: "center", fit: "shrink", margin: 0 });
  });
  card(slide, 0.82, 4.75, 3.65, 1.35, "Инструмент классификации", "`classify_boss_report.py`: XLSX/XLSM/CSV, текстовые колонки, regex + exact terms, debug-колонки.", C.blue, { bodySize: 7.9 });
  card(slide, 4.85, 4.75, 3.65, 1.35, "Инструменты агента", "get_report_context, search_internal_docs, get_owner_registry, risk_policy_check, generate_briefing_pack.", C.green, { bodySize: 7.9 });
  card(slide, 8.88, 4.75, 3.65, 1.35, "Контроль", "RBAC, classification labels, need-to-know, review владельца данных, журнал источников.", C.red, { bodySize: 7.9 });
}

// 5
{
  const slide = pptx.addSlide();
  title(slide, "Классификация", "Система категорий: multi-label вместо выбора одной полки", "Одна строка поручения может одновременно требовать встречи, бюджета, аналитики и технологического решения.", 5);
  const rows = [
    ["Встречи и участие", "совещание, переговоры, презентация", C.blue],
    ["Финансы", "бюджет, capex/opex, инвестиции", C.amber],
    ["Стратегия / Пилоты", "дорожная карта, PoC, опытная эксплуатация", C.green],
    ["Аналитика", "анализ, отчет, показатели, прогноз", C.violet],
    ["Запросы информации", "внутренние подразделения / ФОИВ, ЦБ, ФАС", C.cyan],
    ["Риски", "санкции, комплаенс, инцидент, просрочка", C.red],
    ["ДЗО / Сеть", "дочерние общества, сетевые компании", C.green],
    ["Технологии", "ИИ, импортозамещение, инфраструктура", C.blue],
  ];
  rows.forEach((r, i) => {
    const x = i < 4 ? 0.8 : 6.85;
    const y = 2.18 + (i % 4) * 0.82;
    pill(slide, r[0], x, y, 2.05, r[2], { h: 0.38, fontSize: 7.4 });
    slide.addText(r[1], { x: x + 2.28, y: y + 0.105, w: 3.3, h: 0.14, fontFace: "Aptos", fontSize: 8.5, color: C.slate, fit: "shrink", margin: 0 });
  });
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.82, y: 5.82, w: 5.42, h: 0.64, rectRadius: 0.04, fill: { color: "EAF7F0" }, line: { color: "B7DAC8" } });
  slide.addText("Смешанные распоряжения", { x: 1.08, y: 6.02, w: 1.95, h: 0.13, fontFace: "Aptos", fontSize: 8.3, bold: true, color: C.green, margin: 0 });
  slide.addText("ставится автоматически, если найдено больше одной базовой категории", { x: 3.1, y: 6.02, w: 2.8, h: 0.13, fontFace: "Aptos", fontSize: 8.3, color: C.slate, fit: "shrink", margin: 0 });
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.05, y: 5.82, w: 5.42, h: 0.64, rectRadius: 0.04, fill: { color: "FFF5E7" }, line: { color: "E4C28A" } });
  slide.addText("Иное", { x: 7.32, y: 6.02, w: 0.6, h: 0.13, fontFace: "Aptos", fontSize: 8.3, bold: true, color: C.amber, margin: 0 });
  slide.addText("ставится автоматически, если базовые категории не найдены", { x: 8.05, y: 6.02, w: 3.55, h: 0.13, fontFace: "Aptos", fontSize: 8.3, color: C.slate, fit: "shrink", margin: 0 });
}

// 6
{
  const slide = pptx.addSlide();
  title(slide, "Демо-поручение", "Как один пункт превращается в рабочий пакет", "Пример показывает не реальные данные, а ожидаемую логику сценария.", 6);
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.75, y: 2.08, w: 5.55, h: 1.28, rectRadius: 0.05, fill: { color: C.white }, line: { color: C.line } });
  slide.addText("Поручение руководства", { x: 1.02, y: 2.32, w: 2.2, h: 0.16, fontFace: "Aptos", fontSize: 8.2, bold: true, color: C.blue, margin: 0 });
  slide.addText("«Проанализировать применение LLM в клиентских сервисах, оценить бюджет пилота и подготовить материалы к совещанию с рисками до пятницы»", {
    x: 1.02, y: 2.64, w: 4.95, h: 0.42,
    fontFace: "Aptos Display", fontSize: 13.2, bold: true, color: C.navy,
    fit: "shrink", margin: 0,
  });
  const labels = [
    ["Аналитика", C.violet],
    ["Технологии (ИИ)", C.blue],
    ["Финансы", C.amber],
    ["Пилоты", C.green],
    ["Встречи и участие", C.cyan],
    ["Риски", C.red],
    ["Смешанные распоряжения", C.green],
  ];
  labels.forEach((l, i) => pill(slide, l[0], 7.0 + (i % 2) * 2.45, 2.08 + Math.floor(i / 2) * 0.48, 2.1, l[1], { fontSize: 7.1 }));
  arrow(slide, 6.38, 2.74, 6.86, 2.74, C.blue);
  card(slide, 0.78, 4.18, 2.75, 1.5, "Briefing", "Суть поручения, ожидаемый результат, срок, владелец, открытые вопросы.", C.blue, { bodySize: 7.9 });
  card(slide, 3.75, 4.18, 2.75, 1.5, "Маршрут", "Аналитика, ИТ, финансы, риск-owner, секретариат совещания.", C.green, { bodySize: 7.9 });
  card(slide, 6.72, 4.18, 2.75, 1.5, "Источники", "Регламенты, прошлые поручения, бюджетные витрины, риск-политики.", C.amber, { bodySize: 7.9 });
  card(slide, 9.69, 4.18, 2.75, 1.5, "Audit trail", "matched_categories, matched_patterns, timestamp, ограничения доступа.", C.red, { bodySize: 7.9 });
}

// 7
{
  const slide = pptx.addSlide();
  title(slide, "Границы", "Production-контур: агент готовит и маршрутизирует, но не присваивает полномочия", "Та же логика безопасности, что в сценарии подготовки к срочной встрече.", 7);
  agendaRow(slide, 1, "Доступ", "Проверка роли, need-to-know, уровня классификации и полномочий по объекту поручения.", 0.95, 2.05, C.blue);
  agendaRow(slide, 2, "Данные", "Материалы маркируются источниками, временем актуальности и зонами неопределенности.", 0.95, 3.08, C.green);
  agendaRow(slide, 3, "Решения", "Юридические, финансовые, AML/санкционные и кадровые выводы остаются за владельцами процесса.", 0.95, 4.11, C.amber);
  agendaRow(slide, 4, "Самоулучшение", "Изменение словарей, regex-правил и шаблонов - только через review, тесты и историю изменений.", 0.95, 5.14, C.red);
  slide.addShape(pptx.ShapeType.roundRect, { x: 7.08, y: 2.12, w: 4.9, h: 3.7, rectRadius: 0.05, fill: { color: C.white }, line: { color: C.line } });
  smallLabel(slide, "Критичные варианты завершения", 7.45, 2.48, 2.6, C.blue);
  const endStates = [
    ["DONE_SUCCESS", "поручение размечено, briefing готов"],
    ["DONE_REVIEW_PENDING", "часть данных ждет владельца"],
    ["DONE_PARTIAL", "собрана короткая версия"],
    ["DONE_HANDOFF", "передано ответственному"],
    ["DONE_BLOCKED", "нет прав или данных для старта"],
  ];
  endStates.forEach((s, i) => {
    slide.addText(s[0], { x: 7.45, y: 2.92 + i * 0.48, w: 1.75, h: 0.15, fontFace: "Aptos", fontSize: 7.6, bold: true, color: C.navy, margin: 0 });
    slide.addText(s[1], { x: 9.16, y: 2.92 + i * 0.48, w: 2.35, h: 0.15, fontFace: "Aptos", fontSize: 7.6, color: C.slate, fit: "shrink", margin: 0 });
  });
}

// 8
{
  const slide = pptx.addSlide();
  title(slide, "Пилот", "MVP: агентный контроль поручений руководства на read-only контуре", "Цель пилота - доказать скорость, качество разметки и полезность управленческого briefing без изменения первичных систем.", 8);
  card(slide, 0.72, 2.2, 2.85, 2.7, "Объем", "100-300 строк отчета руководства за выбранный период. Вход: XLSX, текст поручения, краткое содержание, срок, исполнитель.", C.blue);
  card(slide, 3.88, 2.2, 2.85, 2.7, "Интеграции", "Read-only доступ к отчету, справочнику владельцев, базе документов, календарю и журналу прошлых поручений.", C.green);
  card(slide, 7.04, 2.2, 2.85, 2.7, "Метрики", "Точность категорий, доля mixed/other, время подготовки, число уточнений, полнота audit trail, доля ручной доработки.", C.amber);
  card(slide, 10.2, 2.2, 2.35, 2.7, "Следующий шаг", "Подключить review экспертов и regression-тесты на ложные срабатывания правил.", C.red);
  slide.addShape(pptx.ShapeType.roundRect, { x: 0.88, y: 5.55, w: 11.55, h: 0.74, rectRadius: 0.04, fill: { color: C.navy }, line: { color: C.navy } });
  slide.addText("Предлагаемый результат пилота: классифицированный отчет + one-page briefing по смешанным и рискованным поручениям + список правил, которые нужно уточнить перед production.", {
    x: 1.18, y: 5.8, w: 10.9, h: 0.18,
    fontFace: "Aptos", fontSize: 9.4, bold: true, color: C.white,
    fit: "shrink", margin: 0,
  });
}

pptx.writeFile({ fileName: "/Users/amadey/devwork/ouroboros/outputs/manual-20260603-boss-instruction/presentations/boss-instruction-scenario/output/ouroboros-boss-instruction-agent-scenario.pptx" });
