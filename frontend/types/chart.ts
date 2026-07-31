export type ChartValue =
    | string
    | number
    | boolean
    | null;

export interface ChartData {
    type: string;
    title?: string;

    labels?: Array<string | number>;
    values?: number[];

    x?: Array<string | number>;
    y?: number[];

    x_key?: string;
    y_key?: string;

    name_key?: string;
    value_key?: string;

    data?: Array<Record<string, ChartValue>>;

    [key: string]: unknown;
}
