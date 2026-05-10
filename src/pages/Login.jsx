import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Login() {
  const [isSignUp, setIsSignUp] = useState(true)
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>

      {/* 왼쪽 파란 영역 */}
      <div style={{
        width: '40%',
        background: '#5E81F4',
        padding: '48px 40px',
        display: 'flex',
        flexDirection: 'column',
        color: 'white',
        alignItems: 'flex-start'
      }}>
        <h1 style={{ margin: 0, fontSize: '22px', fontWeight: '700', lineHeight: '1.5', textAlign: 'left', color: 'white' }}>
          Welcome to 플랫폼이름.<br />
          {isSignUp ? 'Sign Up to getting started.' : 'Sign In to see latest updates.'}
        </h1>
        <p style={{ fontSize: '13px', opacity: 0.8, marginTop: '12px', textAlign: 'left', color: 'white' }}>
          Enter your details to proceed further
        </p>
        <div style={{
          marginTop: '40px',
          background: 'rgba(255,255,255,0.2)',
          borderRadius: '12px',
          flex: 1,
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          fontWeight: '500',
          color: 'white'
        }}>
          로고 OR 일러스트
        </div>
      </div>

      {/* 오른쪽 흰 영역 */}
      <div style={{
        width: '60%',
        background: '#F8F9FF',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px 80px'
      }}>
        <h2 style={{
          color: '#5E81F4',
          fontSize: '28px',
          fontWeight: '700',
          marginBottom: '32px'
        }}>
          {isSignUp ? 'Sign Up' : 'Sign In'}
        </h2>

        <div style={{ width: '100%', maxWidth: '460px' }}>

          {isSignUp && (
            <div style={{ marginBottom: '28px' }}>
              <label style={{
                fontSize: '12px', color: '#94A3B8',
                display: 'block', marginBottom: '4px', textAlign: 'left'
              }}>이름</label>
              <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #E2E8F0' }}>
                <input
                  type="text"
                  placeholder="Craft UI"
                  style={{
                    flex: 1, border: 'none', padding: '8px 0',
                    fontSize: '14px', outline: 'none',
                    background: 'transparent', textAlign: 'left'
                  }}
                />
                <span style={{ color: '#94A3B8' }}>👤</span>
              </div>
            </div>
          )}

          <div style={{ marginBottom: '28px' }}>
            <label style={{
              fontSize: '12px', color: '#94A3B8',
              display: 'block', marginBottom: '4px', textAlign: 'left'
            }}>이메일</label>
            <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #E2E8F0' }}>
              <input
                type="email"
                placeholder="support@craftui.com"
                style={{
                  flex: 1, border: 'none', padding: '8px 0',
                  fontSize: '14px', outline: 'none',
                  background: 'transparent', textAlign: 'left'
                }}
              />
              <span style={{ color: '#94A3B8' }}>✉️</span>
            </div>
          </div>

          <div style={{ marginBottom: '28px' }}>
            <label style={{
              fontSize: '12px', color: '#94A3B8',
              display: 'block', marginBottom: '4px', textAlign: 'left'
            }}>비밀번호</label>
            <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #E2E8F0' }}>
              <input
                type="password"
                placeholder="Start typing…"
                style={{
                  flex: 1, border: 'none', padding: '8px 0',
                  fontSize: '14px', outline: 'none',
                  background: 'transparent', textAlign: 'left'
                }}
              />
              <span style={{ color: '#94A3B8' }}>🔒</span>
            </div>
          </div>

          {isSignUp && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', marginTop: '8px' }}>
              <input type="checkbox" id="terms" defaultChecked />
              <label htmlFor="terms" style={{ fontSize: '14px', color: '#64748B' }}>
                이용약관에 동의합니다
              </label>
            </div>
          )}

          {!isSignUp && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '24px', marginTop: '8px' }}>
              <input type="checkbox" id="remember" />
              <label htmlFor="remember" style={{ fontSize: '14px', color: '#64748B' }}>
                Remember me
              </label>
            </div>
          )}

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', marginTop: '8px' }}>
            <button
              onClick={() => setIsSignUp(true)}
              style={{
                padding: '12px 40px',
                background: isSignUp ? '#5E81F4' : 'transparent',
                color: isSignUp ? 'white' : '#5E81F4',
                border: '1px solid #5E81F4',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              Sign Up
            </button>
            <button
              onClick={() => {
                if (!isSignUp) navigate('/map')
                else setIsSignUp(false)
              }}
              style={{
                padding: '12px 40px',
                background: !isSignUp ? '#5E81F4' : 'transparent',
                color: !isSignUp ? 'white' : '#5E81F4',
                border: '1px solid #5E81F4',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '600'
              }}
            >
              Sign In
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}

export default Login