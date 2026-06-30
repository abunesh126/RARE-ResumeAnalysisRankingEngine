import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area,
} from 'recharts';

const COLORS = ['#6527BE', '#C2185B', '#2EC4B6', '#F2A65A', '#AD1457', '#E84855', '#9B59B6', '#E8A87C'];

const chartStyle = {
  background: 'white',
  border: '1px solid var(--color-border)',
  borderRadius: 12,
  padding: 20,
  boxShadow: '0 1px 4px rgba(101,39,190,0.06)',
};

const titleStyle = {
  fontSize: 14,
  fontWeight: 700,
  color: 'var(--color-text-primary)',
  marginBottom: 20,
};

const tooltipStyle = {
  background: 'white',
  border: '1px solid var(--color-border)',
  borderRadius: 8,
  boxShadow: '0 4px 16px rgba(101,39,190,0.1)',
  fontSize: 12,
};

export function SkillBarChart({ data }: { data: { skill: string; count: number }[] }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>Skill Distribution</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0ECF8" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11, fill: '#9B95B0' }} axisLine={false} tickLine={false} />
          <YAxis dataKey="skill" type="category" tick={{ fontSize: 11, fill: '#6B6080' }} axisLine={false} tickLine={false} width={75} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(101,39,190,0.05)' }} />
          <Bar dataKey="count" fill="#6527BE" radius={[0, 4, 4, 0]} barSize={10}>
            {data.map((_, i) => (
              <Cell key={i} fill={i % 2 === 0 ? '#6527BE' : '#9B59B6'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ScoreDonutChart({ data }: { data: { range: string; count: number; fill: string }[] }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>Score Distribution</div>
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data} dataKey="count" nameKey="range"
            cx="50%" cy="50%" innerRadius={70} outerRadius={100}
            paddingAngle={3}
          >
            {data.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} formatter={(value, name) => [value, name]} />
          <Legend
            formatter={(value) => <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{value}</span>}
            iconType="circle" iconSize={8}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function ExperienceBarChart({ data }: { data: { range: string; count: number }[] }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>Experience Levels</div>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0ECF8" vertical={false} />
          <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#6B6080' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#9B95B0' }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(101,39,190,0.05)' }} />
          <Bar dataKey="count" fill="#6527BE" radius={[4, 4, 0, 0]} barSize={28} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MonthlyTrendChart({ data }: { data: { month: string; candidates: number; shortlisted: number }[] }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>Monthly Hiring Trend</div>
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="candidateGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6527BE" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#6527BE" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="shortlistGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2EC4B6" stopOpacity={0.15} />
              <stop offset="95%" stopColor="#2EC4B6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0ECF8" vertical={false} />
          <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#6B6080' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#9B95B0' }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend formatter={(v) => <span style={{ fontSize: 11, color: 'var(--color-text-secondary)', textTransform: 'capitalize' }}>{v}</span>} iconType="circle" iconSize={8} />
          <Area type="monotone" dataKey="candidates" stroke="#6527BE" strokeWidth={2} fill="url(#candidateGrad)" dot={{ r: 3, fill: '#6527BE' }} />
          <Area type="monotone" dataKey="shortlisted" stroke="#2EC4B6" strokeWidth={2} fill="url(#shortlistGrad)" dot={{ r: 3, fill: '#2EC4B6' }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function SourcePieChart({ data }: { data: { name: string; value: number }[] }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>Candidate Sources</div>
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} paddingAngle={2}>
            {data.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
          <Legend formatter={(v) => <span style={{ fontSize: 11, color: 'var(--color-text-secondary)' }}>{v}</span>} iconType="circle" iconSize={8} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function HiringFunnelChart({ data }: { data: { stage: string; count: number }[] }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>Hiring Funnel</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, padding: '8px 0' }}>
        {data.map((item, i) => {
          const max = data[0].count;
          const pct = (item.count / max) * 100;
          const hue = ['#6527BE', '#8B42D4', '#A855E8', '#C2185B', '#E84855'][i] || '#6527BE';
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 120, fontSize: 12, color: 'var(--color-text-secondary)', flexShrink: 0 }}>{item.stage}</div>
              <div style={{ flex: 1, height: 24, background: '#F0ECF8', borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: hue, borderRadius: 6, transition: 'width 0.5s ease', display: 'flex', alignItems: 'center', paddingLeft: 8 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: 'white' }}>{item.count}</span>
                </div>
              </div>
              <div style={{ width: 30, fontSize: 12, fontWeight: 600, color: 'var(--color-text-secondary)', textAlign: 'right' }}>{Math.round(pct)}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function LineChartCard({ data, title }: { data: { name: string; value: number }[]; title: string }) {
  return (
    <div style={chartStyle}>
      <div style={titleStyle}>{title}</div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F0ECF8" vertical={false} />
          <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6B6080' }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#9B95B0' }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={tooltipStyle} />
          <Line type="monotone" dataKey="value" stroke="#6527BE" strokeWidth={2} dot={{ r: 3, fill: '#6527BE' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
