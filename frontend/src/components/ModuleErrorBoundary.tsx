
import { Component } from 'react'

import type {
  ErrorInfo,
  ReactNode,
} from 'react'

import {
  AlertTriangle,
  RefreshCw,
} from 'lucide-react'

type Props = {
  children: ReactNode
  resetKey: string
}

type State = {
  hasError: boolean
}

export default class ModuleErrorBoundary extends Component<
  Props,
  State
> {
  state: State = {
    hasError: false,
  }

  static getDerivedStateFromError(): State {
    return {
      hasError: true,
    }
  }

  componentDidCatch(
    error: Error,
    info: ErrorInfo,
  ) {
    if (import.meta.env.DEV) {
      console.error(
        'MachineDoctor module error:',
        error,
        info,
      )
    }
  }

  componentDidUpdate(previousProps: Props) {
    if (
      previousProps.resetKey !== this.props.resetKey &&
      this.state.hasError
    ) {
      this.setState({
        hasError: false,
      })
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <section
          role="alert"
          className="rounded-2xl border border-red-500/20 bg-[#111C2D] p-8 text-center"
        >
          <AlertTriangle
            size={32}
            className="mx-auto mb-4 text-amber-400"
          />

          <h2 className="text-xl font-semibold text-slate-100">
            Unable to load this module
          </h2>

          <p className="mx-auto mt-3 max-w-lg text-sm leading-6 text-slate-400">
            An unexpected interface error occurred.
            Your saved diagnostic records have not been
            modified by this error screen.
          </p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-5 py-2.5 font-semibold text-slate-950 hover:bg-cyan-300"
          >
            <RefreshCw size={17} />
            Reload application
          </button>
        </section>
      )
    }

    return this.props.children
  }
}
