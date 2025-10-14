import { useState, useEffect } from 'react';
import { calls } from '../lib/api';

export default function Calls() {
  const [callList, setCallList] = useState<any[]>([]);

  useEffect(() => {
    loadCalls();
  }, []);

  const loadCalls = async () => {
    const data = await calls.list();
    setCallList(data);
  };

  return (
    <div className="px-4">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Call History</h2>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Driver</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Load</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Phone</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {callList.map((call) => (
              <tr key={call.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{call.driver_name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{call.load_number}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{call.phone_number}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                    {call.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(call.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

