import { ClockType } from "@/lib/clocktype";
import { useState } from "react";
import WelcomePage from "./setup-steps/welcome-page";
import WifiPage from "./setup-steps/wifi-page";
import LoginPage from "./setup-steps/login-page";
import CompletePage from "./setup-steps/complete-page";
import { Button } from "./ui/button";
import Copyright from "./copyright";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import LocalePage from "./setup-steps/locale";
import { API_ENDPOINT } from "@/lib/constants";
import DeviceSettingsPage from "./setup-steps/device-settings";

export default function SetupWizard({ clocktype }: { clocktype: ClockType }) {
  const [currentStep, setCurrentStep] = useState(0);
  const setupMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${API_ENDPOINT}/config/setSetup?setup=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error('Failed to mark setup as complete');
      }
      return response.json();
    },
    onError: (error) => {
      toast.error(error.message);
    },
    onSuccess: () => {
      toast.success('Setup complete');
      window.location.reload();
    }
  });


  const steps = [
    <WelcomePage key="welcome" clocktype={clocktype} />,
    <WifiPage key="wifi" />,
    <LocalePage key="locale" />,
    <LoginPage key="login" />,
    <DeviceSettingsPage key="device-settings" />,
    <CompletePage key="complete" />
  ];

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 flex items-center justify-center">
        <div className="max-w-xl w-full p-6 flex flex-col min-h-[500px]">
          <div className="flex-1 overflow-y-auto mb-8">
            {steps[currentStep]}
          </div>
          <div className="flex flex-col gap-4">
            <div className="flex justify-between">
              <Button
                onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
                disabled={currentStep === 0}
              >
                Back
              </Button>

              <Button
                onClick={() => {
                  if (currentStep === steps.length - 1) {
                    setupMutation.mutate();
                  } else {
                    setCurrentStep(prev => Math.min(steps.length - 1, prev + 1));
                  }
                }}
              >
                {currentStep === steps.length - 1 ? 'Finish' : 'Next'}
              </Button>
            </div>

            <div className="flex justify-center gap-2">
              {steps.map((_, index) => (
                <div
                  key={index}
                  className={`h-2 w-2 rounded-full ${index === currentStep ? 'bg-light-accent dark:bg-dark-accent' : 'bg-light-secondary dark:bg-dark-secondary'
                    }`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
      <div className="py-4 text-center">
        <Copyright clocktype={clocktype} />
      </div>
    </div>
  );
}