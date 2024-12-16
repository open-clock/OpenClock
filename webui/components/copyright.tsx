import { ClockType } from "@/lib/clocktype";

export default function Copyright({ clocktype }: { clocktype: ClockType }) {
    return (
        <p className="text-sm text-light-secondary dark:text-dark-secondary">
          OpenClock {clocktype}. AGPL V3 Licensed.
        </p>
    );
}