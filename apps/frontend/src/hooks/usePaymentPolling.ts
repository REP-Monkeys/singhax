/**
 * Hook to poll for payment completion and update chat automatically
 */

import { useEffect, useState } from 'react';

interface UsePaymentPollingProps {
  sessionId: string | null;
  onPaymentComplete: () => void;
  enabled: boolean;
}

export function usePaymentPolling({ 
  sessionId, 
  onPaymentComplete,
  enabled 
}: UsePaymentPollingProps) {
  const [isPolling, setIsPolling] = useState(false);

  useEffect(() => {
    if (!enabled || !sessionId || isPolling) {
      return;
    }

    console.log('🔄 Starting payment completion polling...');
    setIsPolling(true);

    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    let pollCount = 0;
    const maxPolls = 60; // Poll for 5 minutes (60 * 5 seconds)
    
    const pollInterval = setInterval(async () => {
      pollCount++;
      
      try {
        // Check if there's a new policy confirmed message in the session
        const response = await fetch(`${API_URL}/chat/session/${sessionId}`);
        
        if (response.ok) {
          const data = await response.json();
          
          // Check if last message contains payment success confirmation
          const messages = data.messages || [];
          const lastMessage = messages[messages.length - 1];
          
          if (lastMessage?.role === 'assistant' && 
              lastMessage?.content?.includes('Payment Successful')) {
            console.log('✅ Payment confirmation detected!');
            clearInterval(pollInterval);
            setIsPolling(false);
            onPaymentComplete();
            return;
          }
          
          // Check if there's a confirmed policy
          if (data.policy_confirmed) {
            console.log('✅ Policy confirmed detected!');
            clearInterval(pollInterval);
            setIsPolling(false);
            onPaymentComplete();
            return;
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
      
      // Stop polling after max attempts
      if (pollCount >= maxPolls) {
        console.log('⏱️ Payment polling timeout');
        clearInterval(pollInterval);
        setIsPolling(false);
      }
    }, 5000); // Poll every 5 seconds

    // Cleanup on unmount
    return () => {
      clearInterval(pollInterval);
      setIsPolling(false);
    };
  }, [enabled, sessionId, onPaymentComplete, isPolling]);

  return { isPolling };
}

