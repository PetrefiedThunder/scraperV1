/**
 * Visual cron expression builder for scheduling
 * Makes cron expressions easy for non-technical users
 */

import { useState, useEffect } from 'react';

interface CronBuilderProps {
  value: string;
  onChange: (cronExpression: string) => void;
}

type ScheduleType = 'hourly' | 'daily' | 'weekly' | 'monthly' | 'custom';
type DayOfWeek = 'MON' | 'TUE' | 'WED' | 'THU' | 'FRI' | 'SAT' | 'SUN';

export function CronBuilder({ value, onChange }: CronBuilderProps) {
  const [scheduleType, setScheduleType] = useState<ScheduleType>('daily');
  const [hour, setHour] = useState(9);
  const [minute, setMinute] = useState(0);
  const [dayOfMonth, setDayOfMonth] = useState(1);
  const [daysOfWeek, setDaysOfWeek] = useState<DayOfWeek[]>(['MON']);
  const [customCron, setCustomCron] = useState('0 9 * * *');

  // Parse existing cron expression on mount
  useEffect(() => {
    if (value) {
      // Try to detect schedule type from cron
      if (value.startsWith('0 * * * *')) {
        setScheduleType('hourly');
      } else if (value.match(/^\d+ \d+ \* \* \*$/)) {
        setScheduleType('daily');
        const parts = value.split(' ');
        setMinute(parseInt(parts[0]));
        setHour(parseInt(parts[1]));
      } else if (value.match(/^\d+ \d+ \* \* [0-6,]+$/)) {
        setScheduleType('weekly');
      } else if (value.match(/^\d+ \d+ \d+ \* \*$/)) {
        setScheduleType('monthly');
      } else {
        setScheduleType('custom');
        setCustomCron(value);
      }
    }
  }, [value]);

  // Generate cron expression based on current settings
  useEffect(() => {
    let cron = '';

    switch (scheduleType) {
      case 'hourly':
        cron = '0 * * * *'; // Every hour at minute 0
        break;

      case 'daily':
        cron = `${minute} ${hour} * * *`; // Daily at specified time
        break;

      case 'weekly':
        const dayNumbers = daysOfWeek.map((day) => {
          const days = { MON: 1, TUE: 2, WED: 3, THU: 4, FRI: 5, SAT: 6, SUN: 0 };
          return days[day];
        }).join(',');
        cron = `${minute} ${hour} * * ${dayNumbers}`;
        break;

      case 'monthly':
        cron = `${minute} ${hour} ${dayOfMonth} * *`; // Monthly on specified day
        break;

      case 'custom':
        cron = customCron;
        break;
    }

    onChange(cron);
  }, [scheduleType, hour, minute, dayOfMonth, daysOfWeek, customCron, onChange]);

  const toggleDayOfWeek = (day: DayOfWeek) => {
    setDaysOfWeek((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day]
    );
  };

  const allDays: DayOfWeek[] = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];

  return (
    <div className="space-y-4">
      {/* Schedule Type Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Schedule Frequency
        </label>
        <select
          value={scheduleType}
          onChange={(e) => setScheduleType(e.target.value as ScheduleType)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
        >
          <option value="hourly">Every Hour</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="custom">Custom (Cron Expression)</option>
        </select>
      </div>

      {/* Hourly - No additional options */}
      {scheduleType === 'hourly' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-800">
            Job will run every hour at the start of the hour (XX:00)
          </p>
        </div>
      )}

      {/* Daily - Hour and Minute */}
      {scheduleType === 'daily' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hour (24h)
              </label>
              <input
                type="number"
                min="0"
                max="23"
                value={hour}
                onChange={(e) => setHour(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minute
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={minute}
                onChange={(e) => setMinute(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Runs daily at {hour.toString().padStart(2, '0')}:{minute.toString().padStart(2, '0')}
          </p>
        </div>
      )}

      {/* Weekly - Days selection */}
      {scheduleType === 'weekly' && (
        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hour (24h)
              </label>
              <input
                type="number"
                min="0"
                max="23"
                value={hour}
                onChange={(e) => setHour(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minute
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={minute}
                onChange={(e) => setMinute(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Days of Week
            </label>
            <div className="flex flex-wrap gap-2">
              {allDays.map((day) => (
                <button
                  key={day}
                  type="button"
                  onClick={() => toggleDayOfWeek(day)}
                  className={`px-4 py-2 rounded-lg font-medium transition ${
                    daysOfWeek.includes(day)
                      ? 'bg-purple-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>
          </div>

          <p className="text-sm text-gray-600">
            Runs on {daysOfWeek.join(', ')} at {hour.toString().padStart(2, '0')}:
            {minute.toString().padStart(2, '0')}
          </p>
        </div>
      )}

      {/* Monthly - Day of month */}
      {scheduleType === 'monthly' && (
        <div className="space-y-3">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Day of Month
              </label>
              <input
                type="number"
                min="1"
                max="31"
                value={dayOfMonth}
                onChange={(e) => setDayOfMonth(parseInt(e.target.value) || 1)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Hour (24h)
              </label>
              <input
                type="number"
                min="0"
                max="23"
                value={hour}
                onChange={(e) => setHour(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Minute
              </label>
              <input
                type="number"
                min="0"
                max="59"
                value={minute}
                onChange={(e) => setMinute(parseInt(e.target.value) || 0)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none"
              />
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Runs on day {dayOfMonth} of each month at {hour.toString().padStart(2, '0')}:
            {minute.toString().padStart(2, '0')}
          </p>
        </div>
      )}

      {/* Custom - Direct cron input */}
      {scheduleType === 'custom' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Cron Expression
          </label>
          <input
            type="text"
            value={customCron}
            onChange={(e) => setCustomCron(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none font-mono text-sm"
            placeholder="0 9 * * *"
          />
          <p className="text-xs text-gray-500 mt-2">
            Format: minute hour day month day-of-week
            <br />
            Example: "0 9 * * *" = Every day at 9:00 AM
          </p>
        </div>
      )}
    </div>
  );
}
