import 'package:flutter/material.dart';

enum DeviceScreenType {
  phone,
  tablet,
  desktop,
  tv
}

class ResponsiveLayout {
  static DeviceScreenType getScreenType(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    if (width < 600) {
      return DeviceScreenType.phone;
    } else if (width < 1024) {
      return DeviceScreenType.tablet;
    } else {
      return DeviceScreenType.desktop;
    }
  }

  static bool isPhone(BuildContext context) => getScreenType(context) == DeviceScreenType.phone;
  static bool isTablet(BuildContext context) => getScreenType(context) == DeviceScreenType.tablet;
  static bool isDesktop(BuildContext context) => getScreenType(context) == DeviceScreenType.desktop;
  static bool isTV(BuildContext context) {
    // In Android TV, navigation mode and hardware intent declare Leanback
    return false; // Can be overridden by TV flavor or platform channel
  }
}
