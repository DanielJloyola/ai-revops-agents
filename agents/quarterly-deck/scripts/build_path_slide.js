// One slide, four native line charts, from out/path_numbers.json. Usage: node build_path_slide.js 2026-Q3
const fs = require('fs'); const pptxgen = require('pptxgenjs');
const qtag = process.argv[2].toUpperCase(); const wd = `/home/claude/recap/${qtag}`;
const n = JSON.parse(fs.readFileSync(`${wd}/out/path_numbers.json`));
const Q = n.quarter, months = n.months, pd = n.pulldate.slice(5, 7) + '/' + n.pulldate.slice(8, 10) + '/' + n.pulldate.slice(2, 4), pdd = n.pulldate.slice(5, 7) + '.' + n.pulldate.slice(8, 10) + '.' + n.pulldate.slice(2, 4);
const pres = new pptxgen(); pres.layout = 'LAYOUT_WIDE'; pres.theme = { headFontFace: 'Arial Black', bodyFontFace: 'Arial' };
const NAVY = '1F2A5C', ORG = '7EC8E3', PAID = '1F2A5C', DIR = '8C8C8C', AI = '3A8A7A', OTH = '1F5FBF', FF = '5B3A9E';
const slide = pres.addSlide(); slide.background = { color: 'FFFFFF' };
slide.addShape(pres.ShapeType.rect, { x: 0, y: 0, w: 13.33, h: 0.22, fill: { color: NAVY }, line: { color: NAVY } });
slide.addText(`${Q} PATH: TOTAL FORM FILLS TO MQLS TO SQLS`, { x: 0.4, y: 0.45, w: 11.5, h: 0.6, fontFace: 'Arial Black', fontSize: 30, bold: true, color: NAVY, margin: 0, isTextBox: true });
[['ORGANIC', ORG], ['PAID', PAID], ['DIRECT', DIR], ['AI SEARCH', AI], ['OTHER', OTH]].forEach((l, i) => { const x = 0.45 + i * 2.0;
  slide.addShape(pres.ShapeType.rect, { x, y: 1.3, w: 0.28, h: 0.22, fill: { color: l[1] }, line: { color: l[1] } });
  slide.addText(l[0], { x: x + 0.35, y: 1.25, w: 1.6, h: 0.32, fontSize: 13, bold: true, color: '222222', margin: 0, isTextBox: true }); });
slide.addText(pd, { x: 11.3, y: 1.25, w: 1.6, h: 0.32, fontSize: 12, italic: true, color: '666666', align: 'right', margin: 0, isTextBox: true });
const nice = v => { const steps = [5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]; const s = steps.find(st => st * 4 >= v * 1.1) || 1000; return [Math.ceil(v * 1.1 / s) * s, s]; };
const common = title => ({ showTitle: true, title, titleFontSize: 11, titleColor: '222222', titleFontFace: '+mn-lt', lineSize: 2, lineDataSymbol: 'circle', lineDataSymbolSize: 6,
  showValue: true, dataLabelPosition: 't', dataLabelFontSize: 8, dataLabelColor: '222222', dataLabelFontFace: '+mn-lt', showLegend: false,
  catAxisLabelFontSize: 9, valAxisLabelFontSize: 9, catAxisLabelColor: '444444', valAxisLabelColor: '444444', catAxisLabelFontFace: '+mn-lt', valAxisLabelFontFace: '+mn-lt',
  valGridLine: { color: 'D9D9D9', size: 0.5 }, catGridLine: { style: 'none' }, valAxisMinVal: 0 });
const w = 3.0, y = 1.75, h = 4.35, xs = [0.35, 3.6, 6.85, 10.1], cols = [ORG, PAID, DIR, AI, OTH], chans = ['ORGANIC', 'PAID', 'DIRECT', 'AI SEARCH', 'OTHER'];
const ser = k => chans.map((c, i) => ({ name: c, labels: months, values: n[k][c] }));
const fmt = v => v.toLocaleString('en-US');
const mx = k => Math.max(...chans.map(c => Math.max(...n[k][c])));
let [m1, s1] = nice(Math.max(...n.form_fills.month_total));
slide.addChart(pres.ChartType.line, [{ name: 'Total form fills', labels: months, values: n.form_fills.month_total }], Object.assign({ x: xs[0], y, w, h, chartColors: [FF], valAxisMaxVal: m1, valAxisMajorUnit: s1 }, common(`${Q} TOTAL FORM FILLS = ${fmt(n.totals.form_fills)}`)));
[['mqls', `${Q} TOTAL MQLs = ${fmt(n.totals.mqls)}`], ['net_mqls', `* ${Q} NET MQLs = ${fmt(n.totals.net_mqls)}`], ['sqls', `${Q}  SQLs = ${fmt(n.totals.sqls)}`]].forEach(([k, t], i) => {
  const [m, s] = nice(mx(k));
  slide.addChart(pres.ChartType.line, ser(k), Object.assign({ x: xs[i + 1], y, w, h, chartColors: cols, valAxisMaxVal: m, valAxisMajorUnit: s }, common(t))); });
[3.5, 6.75, 10.0].forEach(x => slide.addShape(pres.ShapeType.line, { x, y: 1.75, w: 0, h: 4.35, line: { color: NAVY, width: 1.5 } }));
slide.addText('*NET MQLS defined as after unqualified leads are omitted (defined on slides 13 & 14)', { x: 7.0, y: 6.45, w: 6.0, h: 0.3, fontSize: 9, color: '333333', align: 'right', margin: 0, isTextBox: true });
slide.addText([{ text: `Source: Salesforce: Lead export (all fields), static pull ${pdd}`, options: { color: '1F5FBF', underline: { style: 'sng' } } }, { text: ` - Data as of ${pdd}`, options: { color: '333333' } }], { x: 0.4, y: 6.75, w: 9, h: 0.3, fontSize: 9, margin: 0, isTextBox: true });
slide.addText('Acme Health', { x: 0.4, y: 6.2, w: 3, h: 0.5, fontSize: 22, color: '2E86C1', margin: 0, isTextBox: true });
slide.addNotes(`Definitions: Form fills = every Lead created in ${Q} ${n.year} (Eastern time). MQLs = Is_MQL__c = TRUE. Net MQLs = Is_MQL__c AND Net_MQL__c = TRUE. SQLs = Is_MQL__c = TRUE AND Status = Qualified. Other = Referral + Drip Campaign + Unknown. Replace the "Acme Health" text with the logo from the deck template.`);
pres.writeFile({ fileName: `${wd}/out/Path_FormFills_MQLs_SQLs.pptx` }).then(() => console.log('saved', `${wd}/out/Path_FormFills_MQLs_SQLs.pptx`));
