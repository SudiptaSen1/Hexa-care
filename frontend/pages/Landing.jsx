import { Button } from '../components/ui/button';
import { Card, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Link } from 'react-router-dom';
import {
  Stethoscope,
  HeartPulse,
  FileHeart,
  ShieldCheck,
  Clock8,
  Syringe,
  ScanHeart,
} from 'lucide-react';
import DarkMode from '../src/DarkMode';

export const Landing = () => {
  return (
    <div className="min-h-screen">
      {/* Header */}
      

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold mb-6">
            Your Health, Our{' '}
            <span className="bg-primary bg-clip-text text-transparent">
              AI-Powered Priority
            </span>
          </h1>
          <p className="text-xl mb-8 leading-relaxed">
            Experience advanced healthcare solutions with intelligent diagnostics, personalized care
            plans, and 24/7 support — all powered by our next-gen AI system trained on medical standards and records.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/dashboard">
              <Button size="lg" className="px-8 py-3 text-lg">
                Get Started
              </Button>
            </Link>
            <Link to="/login">
              <Button variant="outline" size="lg" className="px-8 py-3 text-lg">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Comprehensive Care at Your Fingertips</h2>
          <p className="text-lg max-w-2xl mx-auto">
            From AI-assisted diagnosis to secure health records, HexaCare is your smart health partner.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <Card className="group hover:shadow-lg transition-all duration-300 border-0 backdrop-blur-sm">
            <CardHeader>
              <div className="h-12 w-12 bg-secondary rounded-lg flex items-center justify-center mb-4">
                <Stethoscope className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>AI Diagnostics</CardTitle>
              <CardDescription>
                Get instant symptom analysis and preliminary diagnostics using state-of-the-art AI tools.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="group hover:shadow-lg transition-all duration-300 border-0 backdrop-blur-sm">
            <CardHeader>
              <div className="h-12 w-12 bg-secondary rounded-lg flex items-center justify-center mb-4">
                <FileHeart className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Smart Health Records</CardTitle>
              <CardDescription>
                Manage your health documents digitally, with secure AI analysis for better understanding.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="group hover:shadow-lg transition-all duration-300 border-0 backdrop-blur-sm">
            <CardHeader>
              <div className="h-12 w-12 bg-secondary rounded-lg flex items-center justify-center mb-4">
                <HeartPulse className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Personalized Care Plans</CardTitle>
              <CardDescription>
                Receive tailored treatment and wellness plans based on your lifestyle and health history.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="group hover:shadow-lg transition-all duration-300 border-0 backdrop-blur-sm">
            <CardHeader>
              <div className="h-12 w-12 bg-secondary rounded-lg flex items-center justify-center mb-4">
                <ShieldCheck className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Privacy & Compliance</CardTitle>
              <CardDescription>
                Your data is secured with end-to-end encryption, compliant with health data standards.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="group hover:shadow-lg transition-all duration-300 border-0 backdrop-blur-sm">
            <CardHeader>
              <div className="h-12 w-12 bg-secondary rounded-lg flex items-center justify-center mb-4">
                <Clock8 className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>24/7 Virtual Support</CardTitle>
              <CardDescription>
                Our AI and expert team are always online to assist you — anytime, anywhere.
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="group hover:shadow-lg transition-all duration-300 border-0 backdrop-blur-sm">
            <CardHeader>
              <div className="h-12 w-12 bg-secondary rounded-lg flex items-center justify-center mb-4">
                <Syringe className="h-6 w-6 text-primary" />
              </div>
              <CardTitle>Medication & Vaccine Alerts</CardTitle>
              <CardDescription>
                Get reminders and insights about your prescriptions, vaccines, and upcoming health tasks.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Take Charge of Your Health Today</h2>
          <p className="text-xl text-rose-100 mb-8 max-w-2xl mx-auto">
            Join thousands who trust HexaCare for smarter, safer, and more accessible healthcare.
          </p>
          <Link to="/login">
            <Button size="lg" variant='outline' className="px-8 py-3 text-lg">
              Get Started
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8">
        <div className="container mx-auto px-4 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <span className="text-xl font-bold">HexaCare</span>
          </div>
          <p className="">
            © 2024 HexaCare. All rights reserved. | Privacy Policy | Terms of Service
          </p>
        </div>
      </footer>
    </div>
  );
};
