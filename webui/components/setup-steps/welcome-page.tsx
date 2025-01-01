import { ClockType } from "@/lib/clocktype";

export default function WelcomePage({ clocktype }: { clocktype: ClockType }) {
    return (
        <div>
            <h1 className="text-2xl font-bold mb-4">Welcome to OpenClock {clocktype}</h1>
            <p className="text-light-text dark:text-dark-text">
                This wizard will help you set up your new OpenClock {clocktype}.
            </p>
        </div>
    );
}